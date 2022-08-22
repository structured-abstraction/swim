import sys

from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from swim.media.models import Image, File, Folder
from swim.media.forms import ImageForm, FileForm

#-------------------------------------------------------------------------------
def browser(request, folder_id=None):
    return render(
        request,
        'swim/media/browser.html',
        {
            'title': 'Link Selection',
            'CKEditorFuncNum': request.GET.get('CKEditorFuncNum'),
        }
    )

#-------------------------------------------------------------------------------
def file_upload(request):
    form = FileForm()
    if request.method == "POST":
        form = FileForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.save()
            return render(
                request,
                'swim/media/file-upload-success.html',
                {
                    'file': file,
                    'CKEditorFuncNum': request.GET.get('CKEditorFuncNum'),
                    'type': request.GET.get('type', 'image'),
                }
            )

    return render(
        request,
        'swim/media/file-upload.html',
        {
            'form': form,
            'CKEditorFuncNum': request.GET.get('CKEditorFuncNum'),
            'type': request.GET.get('type', 'image'),
        }
    )

#-------------------------------------------------------------------------------
@csrf_exempt
def image_upload(request):
    form = ImageForm()
    if request.method == "POST":
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save()
            return HttpResponseRedirect(
                "{0}?CKEditorFuncNum={1}&type={2}".format(
                    reverse('swim.media.views.image_view', args=(image.id,)),
                    request.GET.get('CKEditorFuncNum'),
                    request.GET.get('type')
                )
            )

    return render(
        request,
        'swim/media/image-upload.html',
        {
            'form': form,
            'CKEditorFuncNum': request.GET.get('CKEditorFuncNum'),
            'type': request.GET.get('type', 'image'),
        }
    )

#-------------------------------------------------------------------------------
def image_browser(request, folder_id=None):
    folder = None
    images = Image.objects.all()
    if folder_id is not None:
        folder = get_object_or_404(Folder, id=folder_id)
        images = images.filter(folder=folder).distinct()
        folders = Folder.objects.none()
    else:
        images = images.filter(folder__isnull=True).distinct()
        folders = Folder.objects.filter(images__isnull=False).distinct()

    return render(
        request,
        'swim/media/image-browser.html',
        {
            'title': 'Image Selection',
            'CKEditorFuncNum': request.GET.get('CKEditorFuncNum'),
            'type': request.GET.get('type', 'image'),
            'folder': folder,
            'images': images,
            'folders': folders,
        }
    )

#-------------------------------------------------------------------------------
def image_view(request, image_id=None):
    image = get_object_or_404(Image, id=image_id)

    variants = []
    for variant_name, kw in image.image.variant.items():
        variants.append((
            variant_name,
            image.image.generate_variant(
                variant_name, kw['algorithm'], **kw['arguments']),
            kw['arguments']
        ))
    variants.append((
        "Original",
        image.image.url,
        {'width': sys.maxsize, 'height': sys.maxsize})
    )
    return render(
        request,
        'swim/media/image-view.html',
        {
            'title': 'Image Selection',
            'type': request.GET.get('type', 'image'),
            'CKEditorFuncNum': request.GET.get('CKEditorFuncNum'),
            'image': image,
            'variants': sorted(variants, key=lambda d: (d[2].get('width'), d[2].get('height'))),
        }
    )

#-------------------------------------------------------------------------------
def file_browser(request, folder_id=None):
    folder = None
    files = File.objects.all()
    if folder_id is not None:
        folder = get_object_or_404(Folder, id=folder_id)
        files = files.filter(folder=folder).distinct()
        folders = Folder.objects.none()
    else:
        files = files.filter(folder__isnull=True).distinct()
        folders = Folder.objects.filter(files__isnull=False).distinct()

    return render(
        request,
        'swim/media/file-browser.html',
        {
            'title': 'File Selection',
            'CKEditorFuncNum': request.GET.get('CKEditorFuncNum'),
            'type': request.GET.get('type', 'file'),
            'folder': folder,
            'files': files,
            'folders': folders,
        }
    )

#-------------------------------------------------------------------------------
def image_thumb(request, image_id):
    # Using a Context gives the 500 template access to all content
    image = get_object_or_404(Image, pk=image_id)
    return HttpResponse(image.admin_thumbnail())



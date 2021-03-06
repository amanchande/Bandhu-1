from django.contrib import messages
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, JsonResponse
from datetime import datetime
from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.template.defaultfilters import slugify

from accounts.models import User
from bandhuapp.models import Profile
from bandhuapp.templatetags.permissions import is_admin
from .models import (
    Ashram, Activity, Photo, Meeting,
    Attendee, ActivityCategory, Event, HomePage,
)

# Create your views here.

def index(request):
    context = {
        'ashrams': Ashram.objects.all(),
        'content': HomePage.objects.all().first(),
    }
    return render(request, 'ashram.html', context)

@login_required
def create_ashram(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        locality = request.POST.get('locality')
        description = request.POST.get('description')
        address = request.POST.get('address')
        image = request.FILES.get('image')

        # admin = request.POST.get('admin')
        # admin_profile = get_object_or_404(Profile,pk=int(admin))

        if Ashram.objects.filter(name=name, locality=locality).exists():
            messages.error(request, "Ashram with entered Name and Locality already exists.")
            return redirect('ashram:ashram')

        slug = slugify(f'{name} {locality}')
        Ashram.objects.create(name=name, locality=locality, slug=slug,
                              description=description, address=address,
                              image=image)
        return redirect('ashram:AshramDetail', slug)

    return redirect('ashram:ashram')

def ashram_detail(request,slug):
    ashram = get_object_or_404(Ashram,slug=slug)
    categories = ActivityCategory.objects.filter(ashram=ashram)
    events = Event.objects.filter(ashram=ashram)
    meetings = Meeting.objects.filter(ashram=ashram)
    check_admin = is_admin(request.user)

    # if ashram.admin is not None and ashram.admin.user == request.user:
    #     # photos = Photo.objects.filter(ashram=ashram)
    #     check_admin = True
    # else:
    #     photos = Photo.objects.filter(ashram=ashram).filter(approved=True)

    photos = Photo.objects.filter(ashram=ashram)
    unapproved_photos = photos.filter(approved=False)
    photos = photos.filter(approved=True)

    context = {
        'ashram': ashram,
        'categories':categories,
        'events': events,
        'meetings':meetings,
        'photos':photos,
        'check_admin':check_admin,
        'content': HomePage.objects.all().first(),
    }
    return render(request,'ashram_detail.html', context)

@login_required
def add_attendee(request):
    if request.method == 'POST':
        schedule = request.POST.get('schedule')
        topic = request.POST.get('topic')
        slug = request.POST.get('slug')
        print(slug)

        name = request.POST.get('name')
        email = request.POST.get('email')
        contact_no = request.POST.get('contact_no')

        attende = request.POST.get('attendes')
        attendes = attende.split(",")
        print(attendes)
        meeting = Meeting.objects.filter(schedule=schedule).filter(topic=topic).first()

        if name:
            Attendee.objects.create(meeting=meeting,name=name,
                                contact_no=contact_no,email=email)
        else:
            for i in attendes:
                profile = Profile.objects.filter(user__email=i).first()
                print(i,profile)
                Attendee.objects.create(meeting=meeting,profile=profile)
        
        url = '/bandhughar/detail/' + slug +'/'
        return HttpResponseRedirect(url)
    return HttpResponseRedirect('/')
  
@login_required      
def add_meeting(request):
    if request.method == 'POST':
        slug = request.POST.get('slug')
        ashram = get_object_or_404(Ashram,slug=slug)

        topic = request.POST.get('topic')
        agenda = request.POST.get('agenda')
        schedule = request.POST.get('schedule')
        location = request.POST.get('location')
        minutes = request.FILES.get('minutes')

        Meeting.objects.create(minutes=minutes,topic=topic,agenda=agenda,
                                    schedule=schedule,location=location,
                                    ashram=ashram)

        url = '/bandhughar/detail/' + slug +'/'
        return HttpResponseRedirect(url)
    return HttpResponseRedirect('/')

@login_required
def add_activity_category(request):
    if request.method == 'POST':
        slug = request.POST.get('slug')
        name = request.POST.get('name')

        ashram = get_object_or_404(Ashram, slug=slug)

        ActivityCategory.objects.create(ashram=ashram, name=name)

        url = '/bandhughar/detail/' + slug +'/'
        return HttpResponseRedirect(url)
    return HttpResponseRedirect('/')

@login_required
def create_activity(request):
    if request.method == 'POST':
        slug = request.POST.get('slug')
        name = request.POST.get('activity_name')
        category = request.POST.get('category')
        description = request.POST.get('description')
        activity_images = request.FILES.getlist('activity_images')

        ashram = get_object_or_404(Ashram, slug=slug)
        activity_category = get_object_or_404(ActivityCategory, pk=int(category))

        print(ashram,activity_category,category)
        activity = Activity.objects.create(category=activity_category,
                                name=name,description=description)

        for i in activity_images:
            Photo.objects.create(ashram=ashram,picture=i,activity=activity,approved=True)

        url = '/bandhughar/detail/' + slug +'/'
        return HttpResponseRedirect(url)
    return HttpResponseRedirect('/')

@login_required
def add_to_gallery(request):
    if request.method == 'POST':
        slug = request.POST.get('slug')
        activity_images = request.FILES.getlist('gallery_images')
        ashram = get_object_or_404(Ashram,slug=slug)
        print("image =",activity_images)

        for i in activity_images:
            if ashram.admin is not None and ashram.admin.user == request.user:
                Photo.objects.create(ashram=ashram,picture=i,approved=True)
            else:
                Photo.objects.create(ashram=ashram,picture=i)

        url = '/bandhughar/detail/' + slug +'/'
        return HttpResponseRedirect(url)
    return HttpResponseRedirect('/')

@login_required
def admin_approval(request):
    if request.method == 'POST':
        slug = request.POST.get('ashram')
        image_pk = request.POST.get('image')
        status = request.POST.get('status')

        ashram = get_object_or_404(Ashram,slug=slug)
        photo = get_object_or_404(Photo,pk=int(image_pk))
        print(photo)
        if status == "approve":
            photo.approved = True
            photo.save()
        else:
            photo.delete()
        
        print(photo.approved)
        photos = Photo.objects.filter(ashram=ashram)

        data = serializers.serialize('json', photos)
        return JsonResponse(data,safe=False)
    return HttpResponseRedirect('/')

@login_required
def create_event(request):
    if request.method == 'POST':
        slug = request.POST.get('slug')
        thumb = request.FILES.get('event_thumb')
        name = request.POST.get('event_name')
        date = request.POST.get('event_date')
        description = request.POST.get('description')
        
        ashram = get_object_or_404(Ashram,slug=slug)
        Event.objects.create(name=name,ashram=ashram,date=date,
                            description=description,thumb=thumb)

        url = '/bandhughar/detail/' + slug +'/'
        return HttpResponseRedirect(url)
    return HttpResponseRedirect('/')
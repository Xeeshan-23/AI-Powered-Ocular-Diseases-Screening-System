import os
from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from google import genai
from dotenv import load_dotenv

# Local imports from your project
from .ml_engine import predict_image 
from .models import PatientProfile, ScreeningResult, Specialist, ChatMessage, ChatSession

# ==========================================
# 1. Authentication Logic
# ==========================================

def signup_view(request):
    if request.method == 'POST':
        fname = request.POST.get('first_name')
        lname = request.POST.get('last_name')
        email = request.POST.get('email')
        pwd = request.POST.get('password')
        cpwd = request.POST.get('confirm_password')

        if pwd == cpwd:
            if User.objects.filter(username=email).exists():
                messages.error(request, 'Email already registered!')
                return redirect('signup')
            else:
                user = User.objects.create_user(username=email, email=email, password=pwd, first_name=fname, last_name=lname)
                user.save()
                messages.success(request, 'Account created! Please login.')
                return redirect('login')
        else:
            messages.error(request, 'Passwords do not match')
            return redirect('signup')
    return render(request, 'signup.html')

def login_view(request):
    if request.method == 'POST':
        user_name = request.POST.get('username')
        pass_word = request.POST.get('password')
        user = authenticate(request, username=user_name, password=pass_word)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid credentials')
            return redirect('login')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def home_view(request):
    return render(request, 'index.html')

# ==========================================
# 2. Profile & Dashboard Logic
# ==========================================

@login_required(login_url='login')
def dashboard_view(request):
    profile, created = PatientProfile.objects.get_or_create(user=request.user)
    recent_screenings = ScreeningResult.objects.filter(user=request.user).order_by('-date')[:5]
    
    context = {
        'user': request.user,
        'profile': profile,
        'recent_screenings': recent_screenings
    }
    return render(request, 'dashboard.html', context)

@login_required(login_url='login')
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.save()

        profile, created = PatientProfile.objects.get_or_create(user=user)
        profile.address = request.POST.get('address')
        profile.gender = request.POST.get('gender')
        profile.age = request.POST.get('age')
        profile.phone = request.POST.get('phone')
        profile.save()

        messages.success(request, 'Profile details updated successfully!')
        return redirect('dashboard')
    return redirect('dashboard')

@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        old_pass = request.POST.get('old_password')
        new_pass = request.POST.get('new_password')
        confirm_pass = request.POST.get('confirm_password')
        user = request.user
        
        if not user.check_password(old_pass):
            messages.error(request, 'Incorrect current password.')
        elif new_pass != confirm_pass:
            messages.error(request, 'New passwords do not match.')
        else:
            user.set_password(new_pass)
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully!')
        return redirect('dashboard')
    return redirect('dashboard')

# ==========================================
# 3. Medical Screening & Specialists
# ==========================================

@login_required(login_url='login')
def screening_view(request):
    context = {}
    if request.method == 'POST' and request.FILES.get('fundus_image'):
        try:
            image_file = request.FILES['fundus_image']
            fs = FileSystemStorage()
            filename = fs.save(image_file.name, image_file)
            image_url = fs.url(filename)
            
            image_file.seek(0)
            result = predict_image(image_file)
            
            # FIX: We now assign this to a variable (new_scan)
            new_scan = ScreeningResult.objects.create(
                user=request.user,
                image=filename, 
                diagnosis=result['diagnosis'],
                confidence=result['confidence'],
                all_probs=result['all_probs']
            )

            # FIX: We pass the ID of that newly saved scan into the context
            context = {
                'result': result, 
                'image_url': image_url, 
                'show_result': True,
                'screening_id': new_scan.id  # THIS FIXES THE CRASH!
            }
            return render(request, 'screening.html', context)
        except Exception as ex:
            context['error'] = f"Error processing image: {str(ex)}"
            return render(request, 'screening.html', context)
    return render(request, 'screening.html')

@login_required(login_url='login')
def history_view(request):
    screenings = ScreeningResult.objects.filter(user=request.user).order_by('-date')
    return render(request, 'history.html', {'screenings': screenings})

@login_required(login_url='login')
def specialists_view(request):
    return render(request, 'specialists.html')

# ==========================================
# 4. AI Assistant Module (Session-Based)
# ==========================================

@login_required(login_url='login')
def chatbot_page(request):
    session_id = request.GET.get('session_id')
    active_session = None
    
    if session_id:
        active_session = ChatSession.objects.filter(id=session_id, user=request.user).first()

    sessions = ChatSession.objects.filter(user=request.user).order_by('-created_at')
    
    return render(request, 'chatbot.html', {
        'sessions': sessions,
        'active_session': active_session,
    })

@login_required(login_url='login')
def get_chatbot_response(request):
    if request.method == "POST":
        query = request.POST.get('query')
        session_id = request.POST.get('session_id')
        
        load_dotenv()
        api_key = os.getenv('GEMINI_API_KEY')
        # genai.configure(api_key=api_key)
        client = genai.Client(api_key=api_key)

        if query:
            try:
                if session_id and session_id != "":
                    session = ChatSession.objects.get(id=session_id, user=request.user)
                else:
                    session = ChatSession.objects.create(
                        user=request.user, 
                        title=query[:30] + ("..." if len(query) > 30 else "")
                    )

                # model = genai.GenerativeModel('gemini-2.5-flash')
                # ai_response = model.generate_content(query)
                ai_response = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=query
                )
                bot_response_text = ai_response.text

                ChatMessage.objects.create(
                    session=session,
                    user=request.user,  
                    query=query,
                    response=bot_response_text
                )

                return JsonResponse({
                    'reply': bot_response_text,
                    'session_id': session.id
                })

            except Exception as e:
                return JsonResponse({'reply': f"OcularAI Error: {str(e)}"}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required(login_url='login')
def delete_chat_session(request, session_id):
    if request.method == "POST":
        session = ChatSession.objects.filter(id=session_id, user=request.user).first()
        if session:
            session.delete()
            return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

# ==========================
#   5. PDF Report Generation
# ==========================
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import ScreeningResult
from .utils import render_to_pdf

@login_required
def download_screening_pdf(request, screening_id):
    try:
        screening = ScreeningResult.objects.get(id=screening_id, user=request.user)
        # NEW LINE: Fetch the patient's extended profile data
        profile = PatientProfile.objects.filter(user=request.user).first()
    except ScreeningResult.DoesNotExist:
        return HttpResponse("Report not found or unauthorized.", status=404)

    context = {
        'user': request.user,
        'profile': profile,  
        'screening': screening,
    }

    pdf = render_to_pdf('pdf_report.html', context)
    
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"Ocular_Report_{screening.id}_{request.user.username}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    return HttpResponse("Error generating PDF", status=400)


from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Feedback

def submit_feedback(request):
    if request.method == 'POST':
        comment = request.POST.get('comment')
        # UC-11 Normal Flow: Save to system
        Feedback.objects.create(user=request.user, comment=comment)
        # UC-11 Normal Flow: Acknowledge receipt
        messages.success(request, "Thank you! Your feedback has been received.")
        return redirect('dashboard')
    return render(request, 'feedback.html')
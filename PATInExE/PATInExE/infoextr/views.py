from django.shortcuts import render
from infoextr.forms import FormName
from infoextr.models import User
from libraries import PATInExE
from django.core.files import File
from django.http import HttpResponse

# Create your views here.
def index(request):
    return render(request,'infoextr/index.html')

def email_submission(request):
    form = FormName()
    if request.method =="POST":
        form = FormName(request.POST)
        if form.is_valid():
            PATInExE.setNewEmailInFile(form.cleaned_data['emailinput'])
            extractedData = PATInExE.extractInformationFromEmailFile()
            request.session['evaluation_result']=extractedData
            if extractedData['STATUS']=='POTENTIAL':
                try:
                    newInformation=User(Ticketid=extractedData['TICKET-ID'],Dateofjourney=extractedData['DEPART-DATE'],Sheduletime=extractedData['DEPART-TIME'],Source=extractedData['SOURCE'],Destination=extractedData['DESTINATION'],Phonenumber=extractedData['PHONE-NO'],Status=extractedData['STATUS'])
                    newInformation.save()
                except Error as e:
                    return HttpResponse(e.message)
                return show_list(request)
            elif extractedData['STATUS']=='CANCELLED':
                try:
                    existingInformation = User.objects.get(Ticketid=extractedData['TICKET-ID'])
                    existingInformation.Status = "CANCELLED"
                    existingInformation.save()
                except User.DoesNotExist:
                    return show_list(request)
            else:
                return show_list(request)
    else:
        return render(request,'infoextr/email_submission.html',{'form':form})


def show_list(request):
    data_list = User.objects.all()
    data_dic ={'details':data_list}
    if request.method=="POST":
        data_dic['result']=request.session['evaluation_result']
    return render(request,'infoextr/show_list.html',context=data_dic)

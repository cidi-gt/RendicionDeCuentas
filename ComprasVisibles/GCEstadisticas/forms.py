from contact_form.forms import ContactForm
from django import forms
from collections import OrderedDict

class CustomContactForm(ContactForm):
    def __init__(self, request, *args, **kwargs):
        super(CustomContactForm, self).__init__(request=request, *args, **kwargs)
        fields_keyOrder = ['reason', 'name', 'email', 'body', 'url', 'start_date', 'end_date']
        self.fields = OrderedDict((k, self.fields[k]) for k in fields_keyOrder)
        self.fields['name'].label = 'Nombre'
        self.fields['name'].widget = forms.TextInput(attrs={'placeholder':'Nombre'})
        self.fields['email'].label = 'Correo electrónico'
        self.fields['email'].widget = forms.TextInput(attrs={'placeholder':'Correo electrónico'})
        self.fields['body'].label = 'Mensaje'
        self.fields['body'].widget = forms.Textarea(attrs={'placeholder':'Mensaje'})
        self.fields['url'].initial=request.path
    
    
    REASON = (
        ('','Seleccione Motivo'),
        ('anomaly', 'Reportar anomalía'),
        ('data', 'Datos incorrectos'),
        ('suggestion', 'Sugerencia'),
        ('doubt', 'Duda'),
        ('other','Otro')
    )
    reason = forms.ChoiceField(choices=REASON, label='Reason', widget=forms.Select(attrs={'placeholder':'Motivo'}))
    reason.label = 'Motivo'
    url = forms.CharField(max_length=100, widget=forms.HiddenInput())
    start_date = forms.CharField(max_length=100, widget=forms.HiddenInput(), required=False)
    end_date = forms.CharField(max_length=100, widget=forms.HiddenInput(), required=False)
    #captcha = CaptchaField()
    template_name = 'contact_form/contact_form.txt'
    subject_template_name = "contact_form/contact_form_subject.txt"

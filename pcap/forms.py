from django import forms

class PcapUploadForm(forms.Form):
    pcap_file = forms.FileField(label='Escolha um arquivo .PCAP')

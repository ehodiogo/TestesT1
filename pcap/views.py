from django.shortcuts import render
from django.http import HttpResponse
from .forms import PcapUploadForm
from .tasks import dividir_pcap_task, analisar_pcap_task  # Importe a função do Celery para processamento
import os
from django.conf import settings
from django.http import JsonResponse
from celery.result import AsyncResult

# Função de visualização para exibir o formulário de upload
def upload_pcap(request):
    if request.method == 'POST' and request.FILES['pcap_file']:
        form = PcapUploadForm(request.POST, request.FILES)
        if form.is_valid():
            pcap_file = request.FILES['pcap_file']
            
            # Salvar o arquivo no sistema
            file_path = f'uploads/{pcap_file.name}'  # Pasta onde os arquivos serão salvos
            with open(file_path, 'wb') as f:
                for chunk in pcap_file.chunks():
                    f.write(chunk)
            
            # Chama a função de processamento do arquivo PCAP com Celery
            task = analisar_pcap_task.delay(file_path)
            mensagem = f"Tarefa iniciada com sucesso! ID da tarefa: {task.id}"
            return render(request, 'upload_pcap.html', {'form': form, 'mensagem': mensagem})
    else:
        form = PcapUploadForm()

    return render(request, 'upload_pcap.html', {'form': form})

def dividir_pcap_view(request):
    mensagem = ""

    if request.method == "POST":
        try:
            num_part = int(request.POST.get("numPart", 0))
            uploaded_file = request.FILES.get("pcapFile")

            if not uploaded_file:
                raise Exception("Nenhum arquivo .pcap enviado.")

            # Garante que a pasta "uploads" existe
            pasta_uploads = os.path.join(settings.BASE_DIR, "uploads")
            os.makedirs(pasta_uploads, exist_ok=True)

            # Salva o arquivo com o mesmo nome original
            caminho_arquivo = os.path.join(pasta_uploads, uploaded_file.name)

            with open(caminho_arquivo, "wb") as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)

            # Chama task Celery
            task = dividir_pcap_task.delay(
                caminho_arquivo,
                pasta_uploads,  # salva os .pcap divididos na mesma pasta
                num_part
            )

            mensagem = f"Tarefa iniciada com sucesso! ID da tarefa: {task.id}. A partir da parte {num_part}."
        except Exception as e:
            mensagem = f"Erro: {str(e)}"

    return render(request, "dividir_pcap.html", {"mensagem": mensagem})

def verificar_status_task(request, task_id):
    task = AsyncResult(task_id)
    response = {
        'state': task.state,
        'info': task.info if task.info else {}
    }
    return JsonResponse(response)

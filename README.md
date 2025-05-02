## Instalar pacotes do gcc para pcap

sudo apt install libpcap-dev build-essential

## Compilar código C

gcc teste.c -lpcap -lm -o analisador

## Rodar código C Compilado

./analisador PATHDOARQUIVO.PCAP

## Executar criação mapas/grafs (DEPOIS DE TER RODADO ANALISE E CRIADOS OS CSVS)

python3 Graficos.py

## Baixar os reqs do py

pip install -r requirements.txt
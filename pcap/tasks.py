from celery import shared_task
from scapy.all import PcapReader, PcapWriter, IP, IPv6
import os
import pandas as pd
import numpy as np
from scipy.stats import entropy, skew, kurtosis
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict, Counter
from itertools import islice

@shared_task(bind=True)
def dividir_pcap_task(self, pcap_path, pasta_saida, num_part):
    PACOTES_POR_ARQUIVO = 2_000_000
    INICIO_PACOTE = num_part * PACOTES_POR_ARQUIVO
    INICIO_ARQUIVO = num_part

    os.makedirs(pasta_saida, exist_ok=True)

    contador_arquivo = INICIO_ARQUIVO
    arquivos_criados = []
    pacotes_processados = 0

    with PcapReader(pcap_path) as reader:
        for idx, pkt in enumerate(islice(reader, INICIO_PACOTE, None)):
            if idx % PACOTES_POR_ARQUIVO == 0:
                if idx != 0 and writer:
                    writer.close()
                nome_arquivo = os.path.join(pasta_saida, f"parte_{contador_arquivo:03d}.pcap")
                writer = PcapWriter(nome_arquivo, append=False, sync=True)
                arquivos_criados.append(nome_arquivo)
                contador_arquivo += 1

            writer.write(pkt)
            pacotes_processados += 1

            if pacotes_processados % 10_000 == 0:
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "pacotes_processados": pacotes_processados,
                        "arquivos_criados": len(arquivos_criados)
                    }
                )

        if writer:
            writer.close()

    return {
        "mensagem": f"Processamento a partir da parte {num_part} finalizado.",
        "arquivos_criados": arquivos_criados,
        "pacotes_processados": pacotes_processados,
    }

@shared_task(bind=True)
def analisar_pcap_task(self, pcap_path, output_dir="output_csv_graficos", window_size=5):
    os.makedirs(output_dir, exist_ok=True)

    try:
        src_ip_lengths = defaultdict(list)
        src_dst_counter = defaultdict(set)
        window_traffic = defaultdict(int)
        ip_counts = Counter()

        first_timestamp = None
        previous_timestamp = {}
        ipg_list = []

        cdf_lengths = []

        total_packets = 0
        total_bytes = 0

        # Estimar o total de pacotes para % (opcional, se possível)
        try:
            from scapy.all import rdpcap
            total_estimated_packets = len(rdpcap(pcap_path))
        except Exception:
            total_estimated_packets = None  # Não conseguimos estimar

        with PcapReader(pcap_path) as pcap_reader:
            for pkt in pcap_reader:
                if IP in pkt or IPv6 in pkt:
                    try:
                        timestamp = float(pkt.time)
                        length = len(pkt)
                        src_ip = pkt[IP].src if IP in pkt else pkt[IPv6].src
                        dst_ip = pkt[IP].dst if IP in pkt else pkt[IPv6].dst

                        total_packets += 1
                        total_bytes += length

                        ip_counts[src_ip] += 1
                        src_ip_lengths[src_ip].append(length)
                        src_dst_counter[src_ip].add(dst_ip)
                        cdf_lengths.append(length)

                        if src_ip in previous_timestamp:
                            ipg = timestamp - previous_timestamp[src_ip]
                            if ipg >= 0:
                                ipg_list.append((src_ip, ipg))
                        previous_timestamp[src_ip] = timestamp

                        if first_timestamp is None:
                            first_timestamp = timestamp
                        window = int((timestamp - first_timestamp) // window_size)
                        window_traffic[window] += length

                        # Atualizar o progresso a cada 10.000 pacotes
                        if total_packets % 10_000 == 0:
                            percent = 0
                            if total_estimated_packets:
                                percent = (total_packets / total_estimated_packets) * 100
                            self.update_state(
                                state="PROGRESS",
                                meta={
                                    "pacotes_processados": total_packets,
                                    "dados_processados": total_bytes,
                                    "percent": round(percent, 2),
                                }
                            )

                    except Exception:
                        continue

        # Estatísticas
        media_tamanho = {ip: np.mean(lengths) for ip, lengths in src_ip_lengths.items()}
        bytes_por_ip = {ip: np.sum(lengths) for ip, lengths in src_ip_lengths.items()}

        total_ip_counts = sum(ip_counts.values())
        probs = np.array(list(ip_counts.values())) / total_ip_counts
        entropia_ips = entropy(probs)

        ipg_df = pd.DataFrame(ipg_list, columns=['src_ip', 'ipg'])
        ipg_stats = ipg_df.groupby('src_ip')['ipg'].agg(['mean', 'std']).dropna()

        skew_ipg = skew(ipg_df['ipg'])
        kurt_ipg = kurtosis(ipg_df['ipg'])

        dst_unicos_por_src = {ip: len(dsts) for ip, dsts in src_dst_counter.items()}
        horizontal_scan = {ip: count for ip, count in dst_unicos_por_src.items() if count > 20}

        # Exportar CSVs
        pd.Series(media_tamanho).to_csv(os.path.join(output_dir, "media_tamanho_por_ip.csv"))
        pd.Series(bytes_por_ip).to_csv(os.path.join(output_dir, "bytes_por_ip.csv"))
        ipg_stats.to_csv(os.path.join(output_dir, "ipg_por_ip.csv"))
        pd.Series(ip_counts).nlargest(10).to_csv(os.path.join(output_dir, "top_10_ips.csv"))
        pd.Series(window_traffic).sort_index().to_csv(os.path.join(output_dir, "trafego_temporal.csv"))
        pd.Series(horizontal_scan).to_csv(os.path.join(output_dir, "horizontal_scan.csv"))

        # Gráficos
        sns.set_style("whitegrid")

        # CDF
        cdf_x = np.sort(cdf_lengths)
        cdf_y = np.arange(1, len(cdf_x) + 1) / len(cdf_x)

        plt.figure(figsize=(8, 5))
        plt.plot(cdf_x, cdf_y)
        plt.title('CDF do Tamanho dos Pacotes')
        plt.xlabel('Tamanho (bytes)')
        plt.ylabel('Probabilidade Acumulada')
        plt.grid()
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "cdf_tamanho_pacotes.png"))
        plt.close()

        # Tráfego Temporal
        plt.figure(figsize=(10, 4))
        pd.Series(window_traffic).sort_index().plot()
        plt.title('Tráfego por Janela de Tempo')
        plt.xlabel('Janela (s)')
        plt.ylabel('Bytes')
        plt.grid()
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "trafego_temporal.png"))
        plt.close()

        # Top IPs
        top_ips = pd.Series(ip_counts).nlargest(10)
        plt.figure(figsize=(10, 6))
        sns.barplot(x=top_ips.values, y=top_ips.index, palette='rocket')
        plt.title('Top 10 IPs Mais Ativos (Número de Pacotes)')
        plt.xlabel('Quantidade de Pacotes')
        plt.ylabel('IP de Origem')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "barras_top_ips.png"))
        plt.close()

        return {
            "status": "sucesso",
            "entropia_ips": entropia_ips,
            "skew_ipg": skew_ipg,
            "kurt_ipg": kurt_ipg,
            "output_dir": output_dir,
            "total_pacotes": total_packets,
            "total_bytes": total_bytes,
        }

    except Exception as e:
        return {
            "status": "erro",
            "mensagem": str(e)
        }

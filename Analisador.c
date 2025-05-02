#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pcap.h>
#include <netinet/ip.h>
#include <netinet/if_ether.h>
#include <arpa/inet.h>
#include <math.h>

#define MAX_IPS 1024
#define TIME_BINS 10000

typedef struct {
    char ip[INET_ADDRSTRLEN];
    int packet_count;
    double total_bytes;
    double last_timestamp;
    double ipg_sum;
    double ipg_sq_sum;
    int ipg_count;
} IPStats;

typedef struct {
    int second;
    int packet_count;
} TimeBin;

IPStats stats[MAX_IPS];
int ip_count = 0;

TimeBin timeline[TIME_BINS];
int timeline_count = 0;

double total_packets = 0.0;

int find_or_add_ip(const char *ip) {
    for (int i = 0; i < ip_count; i++) {
        if (strcmp(stats[i].ip, ip) == 0)
            return i;
    }
    if (ip_count >= MAX_IPS) return -1;
    strncpy(stats[ip_count].ip, ip, INET_ADDRSTRLEN);
    stats[ip_count].packet_count = 0;
    stats[ip_count].total_bytes = 0;
    stats[ip_count].last_timestamp = 0;
    stats[ip_count].ipg_sum = 0;
    stats[ip_count].ipg_sq_sum = 0;
    stats[ip_count].ipg_count = 0;
    return ip_count++;
}

void process_packet(const struct pcap_pkthdr *header, const u_char *packet) {
    struct ether_header *eth = (struct ether_header *) packet;
    if (ntohs(eth->ether_type) != ETHERTYPE_IP) return;

    struct ip *ip_hdr = (struct ip *)(packet + sizeof(struct ether_header));
    char src_ip[INET_ADDRSTRLEN];
    inet_ntop(AF_INET, &(ip_hdr->ip_src), src_ip, INET_ADDRSTRLEN);

    int idx = find_or_add_ip(src_ip);
    if (idx == -1) return;

    stats[idx].packet_count++;
    stats[idx].total_bytes += header->len;
    total_packets++;

    double ts = header->ts.tv_sec + header->ts.tv_usec / 1000000.0;
    if (stats[idx].last_timestamp != 0) {
        double ipg = ts - stats[idx].last_timestamp;
        stats[idx].ipg_sum += ipg;
        stats[idx].ipg_sq_sum += ipg * ipg;
        stats[idx].ipg_count++;
    }
    stats[idx].last_timestamp = ts;

    int sec = header->ts.tv_sec;
    if (timeline_count == 0 || timeline[timeline_count - 1].second != sec) {
        if (timeline_count < TIME_BINS) {
            timeline[timeline_count].second = sec;
            timeline[timeline_count].packet_count = 1;
            timeline_count++;
        }
    } else {
        timeline[timeline_count - 1].packet_count++;
    }
}

double log2_wrapper(double x) {
    return log(x) / log(2.0);
}

void calcular_entropia() {
    double entropia = 0.0;
    for (int i = 0; i < ip_count; i++) {
        if (stats[i].packet_count == 0) continue;
        double p = stats[i].packet_count / total_packets;
        entropia -= p * log2_wrapper(p);
    }
    printf("Entropia dos IPs de origem: %.4f\n", entropia);
}

int cmp_packet_count(const void *a, const void *b) {
    IPStats *ipA = (IPStats *)a;
    IPStats *ipB = (IPStats *)b;
    return ipB->packet_count - ipA->packet_count;
}

void export_csv() {
    FILE *f = fopen("estatisticas.csv", "w");
    fprintf(f, "IP,Pacotes,Bytes,IPG Medio,IPG Desvio\n");

    for (int i = 0; i < ip_count; i++) {
        double media = (stats[i].ipg_count > 0) ? stats[i].ipg_sum / stats[i].ipg_count : 0.0;
        double desvio = 0.0;
        if (stats[i].ipg_count > 0) {
            double media_quad = stats[i].ipg_sq_sum / stats[i].ipg_count;
            desvio = sqrt(media_quad - media * media);
        }

        fprintf(f, "%s,%d,%.0f,%.6f,%.6f\n",
                stats[i].ip,
                stats[i].packet_count,
                stats[i].total_bytes,
                media,
                desvio);
    }
    fclose(f);

    FILE *t = fopen("timeline.csv", "w");
    fprintf(t, "Segundo,Pacotes\n");
    for (int i = 0; i < timeline_count; i++) {
        fprintf(t, "%d,%d\n", timeline[i].second, timeline[i].packet_count);
    }
    fclose(t);
}

int main(int argc, char *argv[]) {
    if (argc != 2) {
        printf("Uso: %s arquivo.pcap\n", argv[0]);
        return 1;
    }

    char errbuf[PCAP_ERRBUF_SIZE];
    pcap_t *handle = pcap_open_offline(argv[1], errbuf);
    if (!handle) {
        fprintf(stderr, "Erro ao abrir %s: %s\n", argv[1], errbuf);
        return 2;
    }

    struct pcap_pkthdr *header;
    const u_char *packet;
    int res;
    int qtPkts = 0;

    while ((res = pcap_next_ex(handle, &header, &packet)) >= 0) {
        if (res == 0) continue;
        process_packet(header, packet);
        qtPkts++;
        if (qtPkts % 10000 == 0) {
            printf("Processados %d pacotes.\n", qtPkts);
        }
    }

    pcap_close(handle);

    qsort(stats, ip_count, sizeof(IPStats), cmp_packet_count);

    printf("Top 10 IPs mais ativos:\n");
    for (int i = 0; i < ip_count && i < 10; i++) {
        printf("%s - %d pacotes\n", stats[i].ip, stats[i].packet_count);
    }

    calcular_entropia();
    export_csv();

    printf("Pacotes processados: %d\n", qtPkts);
    printf("Estatísticas exportadas para 'estatisticas.csv' e 'timeline.csv'.\n");
    return 0;
}

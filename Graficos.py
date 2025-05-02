import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Estilo visual
sns.set(style="whitegrid")
plt.rcParams["figure.figsize"] = (10, 6)

# ---------- Leitura dos dados ----------
estatisticas = pd.read_csv("estatisticas.csv")
timeline = pd.read_csv("timeline.csv")

# ---------- Gráfico 1: Top 10 IPs por Pacotes ----------
estatisticas_top = estatisticas.sort_values(by="Pacotes", ascending=False).head(10)
plt.figure()
sns.barplot(data=estatisticas_top, x="Pacotes", y="IP", palette="Reds_r")
plt.title("Top 10 IPs por quantidade de pacotes")
plt.xlabel("Pacotes (Milhão)")
plt.ylabel("IP")
plt.tight_layout()
plt.savefig("grafico_top_ips.png")
plt.close()

# ---------- Gráfico 2: Linha do tempo do tráfego ----------
plt.figure()
sns.lineplot(data=timeline, x="Segundo", y="Pacotes", marker="o", color="darkred")
plt.title("Tráfego ao longo do tempo (1 segundo)")
plt.xlabel("Tempo (s)")
plt.ylabel("Pacotes")
plt.tight_layout()
plt.savefig("grafico_tempo.png")
plt.close()

# ---------- Gráfico 3: Boxplot do IPG Médio ----------
plt.figure()
sns.boxplot(data=estatisticas, x="IPG Medio", color="salmon")
plt.title("Distribuição do IPG Médio")
plt.xlabel("IPG Médio (segundos)")
plt.tight_layout()
plt.savefig("grafico_ipg_medio.png")
plt.close()

# ---------- Gráfico 4: Top 10 IPs com maior IPG Médio ----------
top_ipg = estatisticas[estatisticas["Pacotes"] > 1].sort_values(by="IPG Medio", ascending=False).head(10)
plt.figure()
sns.barplot(data=top_ipg, x="IPG Medio", y="IP", palette="coolwarm")
plt.title("Top 10 IPs com maior IPG médio")
plt.xlabel("IPG Médio (segundos)")
plt.ylabel("IP")
plt.tight_layout()
plt.savefig("grafico_top_ipg.png")
plt.close()

# ---------- Gráfico 5: Dispersão IPG Médio vs Desvio ----------
plt.figure(figsize=(8, 6))
plt.scatter(estatisticas["IPG Medio"], estatisticas["IPG Desvio"], alpha=0.7, color='dodgerblue')
plt.title("IPG Médio vs Desvio Padrão")
plt.xlabel("IPG Médio (s)")
plt.ylabel("Desvio Padrão do IPG (s)")
plt.grid(True)
plt.tight_layout()
plt.savefig("grafico_dispersion_ipg.png")
plt.close()

# ---------- Verificando os dados antes de gerar o gráfico 6 ----------
# Exibe as primeiras linhas do DataFrame para verificar se os dados estão corretos
print("Primeiras linhas do DataFrame de Timeline:")
print(timeline.head())

# ---------- Gráfico 6: Mapa de calor IP x Tempo (se aplicável) ----------
# Verifica se o 'Segundo' está presente e se existem colunas adicionais para os IPs
if "Segundo" in timeline.columns and any(col != "Segundo" for col in timeline.columns):
    # Prepara os dados para o mapa de calor
    heatmap_data = timeline.set_index("Segundo").T  # Transposta para ter IPs nas linhas e tempo nas colunas
    
    # Verifica se a matriz de dados tem pelo menos uma linha e uma coluna
    if not heatmap_data.empty:
        plt.figure(figsize=(12, 8))
        sns.heatmap(heatmap_data, cmap="Reds", linewidths=0.5)
        plt.title("Mapa de Calor: Atividade dos IPs ao longo do tempo")
        plt.xlabel("Tempo (s)")
        plt.ylabel("IP")
        plt.tight_layout()
        plt.savefig("grafico_mapa_calor.png")
        plt.close()
    else:
        print("⚠️ Dados insuficientes para gerar o mapa de calor.")
else:
    print("⚠️ Estrutura de dados inválida para o mapa de calor.")

# ---------- Final ----------
print("✅ Gráficos gerados com sucesso:")
print("- grafico_top_ips.png")
print("- grafico_tempo.png")
print("- grafico_ipg_medio.png")
print("- grafico_top_ipg.png")
print("- grafico_dispersion_ipg.png")
print("- grafico_mapa_calor.png (se aplicável)")

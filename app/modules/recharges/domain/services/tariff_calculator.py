"""
Logica de Desdobramento Tarifario CREDELEC (FUNAE/EDM Mocambique)

A tarifa de electricidade em Mocambique segue a estrutura da FUNAE/EDM:
- IVA: 17%
- Taxa de Radio: valor fixo mensal
- Taxa de Lixo: valor fixo mensal
- Divida: se existir saldo devedor do utilizador
- Energia: o restante converte-se em kWh à tarifa vigente

Nota: Os valores aqui são ilustrativos. Em producao, devem ser carregados
a partir de uma tabela de configuracao no Supabase (para permitir actualizacao
sem redeployment).
"""

# ─── Constantes Tarifarias (em MZN) ──────────────────────────────────────────
# Valores de referencia CREDELEC — actualizar conforme tabela EDM vigente
TARIFA_KWH = 6.50          # MZN por kWh (bloco residencial basico)
TAXA_IVA = 0.17            # 17%
TAXA_RADIO = 15.00         # MZN/mes (cobranca unica no mes)
TAXA_LIXO = 10.00          # MZN/mes (cobranca unica no mes)
MONTANTE_MINIMO_MZN = 50.0 # Recarga minima permitida (RN01)


def calcular_desdobramento(
    montante_total: float,
    divida_pendente: float = 0.0,
    is_primeira_compra_mes: bool = False,
) -> dict:
    """
    Calcula o desdobramento tarifario CREDELEC para um dado montante.

    Args:
        montante_total:       Valor total pago pelo utilizador em MZN.
        divida_pendente:      Saldo devedor existente (se aplicavel).
        is_primeira_compra_mes: Se True, aplica as taxas fixas do mes.

    Returns:
        Dicionário com todos os componentes do desdobramento e kWh resultante.
    """
    if montante_total < MONTANTE_MINIMO_MZN:
        raise ValueError(
            f"Montante mínimo de recarga é {MONTANTE_MINIMO_MZN} MZN. "
            f"Recebido: {montante_total} MZN."
        )

    restante = montante_total

    # 1. Amortizar divida pendente primeiro
    divida_paga = min(divida_pendente, restante)
    restante -= divida_paga

    # 2. Taxas fixas mensais (so na primeira recarga do mes)
    tx_radio = 0.0
    tx_lixo = 0.0
    if is_primeira_compra_mes:
        if montante_total == 100.0:
            tx_lixo = 50.0
            restante -= tx_lixo
            tx_radio = min(TAXA_RADIO, restante)
            restante -= tx_radio
        else:
            tx_radio = min(TAXA_RADIO, restante)
            restante -= tx_radio
            tx_lixo = min(TAXA_LIXO, restante)
            restante -= tx_lixo

    # 3. IVA calculado sobre o montante de energia (restante apos taxas/divida)
    # Formula: montante_liquido = restante / (1 + IVA)
    montante_energia_liquido = restante / (1 + TAXA_IVA)
    iva = restante - montante_energia_liquido

    # 4. Converter energia em kWh
    kwh_calculado = montante_energia_liquido / TARIFA_KWH

    return {
        "montante_total": round(montante_total, 2),
        "val_energia": round(montante_energia_liquido, 2),
        "iva": round(iva, 2),
        "divida_paga": round(divida_paga, 2),
        "tx_radio": round(tx_radio, 2),
        "tx_lixo": round(tx_lixo, 2),
        "kwh_calculado": round(kwh_calculado, 4),
    }

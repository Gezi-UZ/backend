"""
Lógica de Desdobramento Tarifário CREDELEC (FUNAE/EDM Moçambique)

A tarifa de electricidade em Moçambique segue a estrutura da FUNAE/EDM:
- IVA: 17%
- Taxa de Rádio: valor fixo mensal
- Taxa de Lixo: valor fixo mensal
- Dívida: se existir saldo devedor do utilizador
- Energia: o restante converte-se em kWh à tarifa vigente

Nota: Os valores aqui são ilustrativos. Em produção, devem ser carregados
a partir de uma tabela de configuração no Supabase (para permitir actualização
sem redeployment).
"""

# ─── Constantes Tarifárias (em MZN) ──────────────────────────────────────────
# Valores de referência CREDELEC — actualizar conforme tabela EDM vigente
TARIFA_KWH = 6.50          # MZN por kWh (bloco residencial básico)
TAXA_IVA = 0.17            # 17%
TAXA_RADIO = 15.00         # MZN/mês (cobrança única no mês)
TAXA_LIXO = 10.00          # MZN/mês (cobrança única no mês)
MONTANTE_MINIMO_MZN = 50.0 # Recarga mínima permitida (RN01)


def calcular_desdobramento(
    montante_total: float,
    divida_pendente: float = 0.0,
    is_primeira_compra_mes: bool = False,
) -> dict:
    """
    Calcula o desdobramento tarifário CREDELEC para um dado montante.

    Args:
        montante_total:       Valor total pago pelo utilizador em MZN.
        divida_pendente:      Saldo devedor existente (se aplicável).
        is_primeira_compra_mes: Se True, aplica as taxas fixas do mês.

    Returns:
        Dicionário com todos os componentes do desdobramento e kWh resultante.
    """
    if montante_total < MONTANTE_MINIMO_MZN:
        raise ValueError(
            f"Montante mínimo de recarga é {MONTANTE_MINIMO_MZN} MZN. "
            f"Recebido: {montante_total} MZN."
        )

    restante = montante_total

    # 1. Amortizar dívida pendente primeiro
    divida_paga = min(divida_pendente, restante)
    restante -= divida_paga

    # 2. Taxas fixas mensais (só na primeira recarga do mês)
    tx_radio = 0.0
    tx_lixo = 0.0
    if is_primeira_compra_mes:
        tx_radio = min(TAXA_RADIO, restante)
        restante -= tx_radio
        tx_lixo = min(TAXA_LIXO, restante)
        restante -= tx_lixo

    # 3. IVA calculado sobre o montante de energia (restante após taxas/dívida)
    # Fórmula: montante_liquido = restante / (1 + IVA)
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

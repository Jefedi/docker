# Rental Yield Calculation Reference

## Current Parameters (May 2026 — Le Havre)

| Parameter | Value | Source |
|-----------|-------|--------|
| Notaire (ancien) | 7.5% | cafpi.fr, pretto.fr |
| Mortgage rate 25 ans | 3.49% | Normandie, cafpi.fr May 2026 |
| Loyer médian/m² | 13 €/mois | Capital.fr, SeLoger, OuestFrance-Immo |
| Vacance locative | 5% | Standard |
| Entretien | 5% des loyers | Standard |
| Assurance PNO | 150 €/an | Standard |
| Frais de gestion (optionnel) | 7-8% des loyers | Si agence |

## Yield Calculation (Python)

```python
def analyze_property(price, surface, charges_annuelles, taxe_fonciere,
                     dpe=None, loyer_reel=None, loyer_estime=13):
    NOTAIRE = 0.075
    TAUX = 0.0349  # 25 ans
    ANNUITE = TAUX / 12
    ASSURANCE = 150
    VACANCE = 0.05
    ENTRETIEN = 0.05

    notaire = price * NOTAIRE
    total_acq = price + notaire

    if loyer_reel:
        monthly_rent = loyer_reel
        rent_source = "réel"
    else:
        monthly_rent = surface * loyer_estime
        rent_source = "estimé"

    gross_annual = monthly_rent * 12
    net_annual = gross_annual * (1 - VACANCE - ENTRETIEN) - charges_annuelles - taxe_fonciere - ASSURANCE

    gross_yield = (gross_annual / price) * 100
    net_yield = (net_annual / total_acq) * 100

    n_payments = 25 * 12
    monthly = total_acq * (ANNUITE * (1+ANNUITE)**n_payments) / ((1+ANNUITE)**n_payments - 1)
    cashflow = (net_annual - monthly * 12) / 12

    return {
        "total_acquisition": round(total_acq),
        "monthly_rent": round(monthly_rent),
        "rent_source": rent_source,
        "gross_yield": round(gross_yield, 2),
        "net_yield": round(net_yield, 2),
        "monthly_payment": round(monthly),
        "cashflow": round(cashflow),
        "dpe": dpe
    }
```

## DPE → Energy €/year Conversion (approximate)

| DPE | kWh/m²·an | Annual cost estimate (30m²) |
|-----|-----------|-----------------------------|
| A | ≤ 70 | < 250 € |
| B | 71-110 | 250-400 € |
| C | 111-180 | 400-600 € |
| D | 181-250 | 600-850 € |
| E | 251-330 | 850-1,100 € |
| F | 331-420 | 1,100-1,400 € |
| G | > 420 | > 1,400 € |

## Key Considerations for French Buy-to-Let

### Taxes
- **Taxe foncière**: 500-1,100 €/an for small apartments
- **Impôt sur le revenu foncier**: You pay income tax on net rental income (after charges, notaire amortization). Different regimes: micro-foncier (30% flat deduction up to 15k€ revenue) vs régime réel (deduct actual costs).
- **Plus-value**: Capital gains tax when selling (15% + 17.2% social charges, reduced by holding period)

### Régime LMNP (Loueur Meublé Non Professionnel)
- Furnished rental is often more tax-efficient than unfurnished
- Allows amortization of the property and furniture, reducing taxable income significantly
- Requires declaring at the Greffe du Tribunal de Commerce
- Consult a comptable spécialisé LMNP

### Rental Regulations
- **Loi ALUR / Climat et Résilience**: DPE G banned since 2025, F and E banned by 2028
- **Encadrement des loyers**: Le Havre may have rent control — check before setting rent
- **Loi Pinel**: Tax reduction for new-build investments (ended or modified — check current status)
- **Loi Denormandie**: Similar to Pinel for old buildings with renovation — check if Le Havre is eligible

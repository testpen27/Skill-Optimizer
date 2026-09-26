# Reading the speech from the text alone

How the rebuild finds every person-level measure in a budget speech without going to the web. Three scripts, one ledger:

| Step | Script | What it does |
|---|---|---|
| Split | `scripts/split-source.js` | Breaks the speech into numbered **units**: each paragraph's opening (`P184`) and each bullet (`P184.2`), each Lampiran I entry (`L1.29`) and item (`L1.29.3`), and each Lampiran II entry (`L2.36`). Fails if paragraph or Lampiran I numbering has a gap, because a gap means lost text. |
| Score | `scripts/text-signals.js` | Marks each unit with the signals it contains and **flags** the ones likely to affect a person. Flagging only orders the reading. It never decides anything. |
| Learn | `scripts/learn-programmes.js` | Learns citizen programme names from past speeches (`references/programmes.json`). It lists which programmes appear every year, which dropped out of the latest text, and which are new. A unit that names a known programme is flagged. |
| Account | `scripts/coverage.js` | Checks the ledger: every unit has a decision, flagged units aren't bulk-excluded, every brain item has a source unit, and no `gap`/`ask` remains at hand-over. |

## Why a ledger and not keywords

Keywords only find wording someone already thought of. The 2026 brain cites 56 of the speech's 251 paragraphs; nothing recorded whether the other 195 were read. Two items it missed were ones the user cares about: the Langkawi and Labuan vehicle tax exemption cap (Perenggan 27) and PERKESO dialysis rates (Perenggan 170). A ledger with a row per unit turns "did anyone notice it?" into "was it decided?", and a script can check that.

## How the signals were derived

The 2026 brain's 94 items were matched to the unit each came from (90 source units). Word frequencies in those units were then compared with the other 1,189 units of Ucapan Belanjawan 2026.

**What marks a person-level measure** (share of source units vs other units): individual tax wording, such as *pelepasan cukai*, *cukai pendapatan individu*, *pengecualian duti* and *tahun taksiran*; per-person amounts written as digits before *ringgit*/*sen* (not *bilion ringgit*); *sebulan* and *setahun*; *sehingga RM…*; named recipients, such as *ibu bapa*, *murid*, *OKU*, *warga emas* and *penjawat awam*; eligibility words, such as *yang layak*, *terhad*, *menerima* and *diberikan*; and help aimed at a group (*kepada 5,000 ibu tunggal*, *untuk anak muda*).

**What marks something else**: infrastructure (*naik taraf*, *jalan*, *sungai*, *bekalan air*, *projek*), companies and investment (*syarikat*, *pelaburan*, *dana*, *industri*), macro figures (*bilion*, *KDNK*, *defisit*) and speech rhetoric (*kita*, *ekonomi*). *Naik* on its own is a trap, because it is usually *naik taraf* (upgrade), not a price rise.

**Result on 2026** (flag threshold `FLAG_AT = 2`): about a third of units are flagged, and 85 of the 90 source units are among them. Of the 5 unflagged, 2 were matching errors. The other 3 are programme announcements with no amount or group named, which is why the ledger, not the score, is the guarantee.

**Checked on 2025 and 2024** (not used for tuning): units that name STR, SARA, mySalam, i-Suri, PTPTN, Rahmah, tobacco, alcohol, Langkawi or Labuan are mostly flagged. The unflagged ones are allocation totals, Labuan infrastructure and rhetoric. One real miss ("mySalam juga diperluas … penyakit jarang jumpa", 2025) is what led to the learned programme list.

## What three years of speeches taught

- **Lampiran I carries measures the speech never mentions.** In 2026 these include the pensioners' special appreciation payment, APEL.Q INTAN (50% of study costs, up to RM15,000), BIPK/BIPAC incentives and LiKES. Read Lampiran I as a source in its own right, not only for amounts.
- **One paragraph holds many measures.** Perenggan 184 holds cigarette, cigar and heated-tobacco duty, nicotine-replacement exemptions and alcohol duty. The lead-in line ("Agenda Nasional Malaysia Sihat diperkasa") names none of them. Bullets are separate units for this reason.
- **Area-based tax measures sit in governance sections.** The Langkawi and Labuan vehicle exemption cap sits under *Tekad Satu: Tatakelola*, among anti-leakage measures, not under cost of living.
- **Programmes recur.** 22 names appear in all three years, including STR, SARA, i-Suri, mySalam, i-Saraan, SKSPS, KAFA, the paddy price subsidy and the fishermen's catch incentive. A programme that was in last year's speech and is missing from this year's is a question for the user. Don't assume it ended, and don't look it up on the web.

## Extending the signals

When a rebuild finds a person-level measure that wasn't flagged, add the phrase that should have caught it to the right group in `text-signals.js`. Re-run `split-source.js` on all past speeches and check that flagged share stays near a third. The same applies when a flagged unit is plainly not for people. This is the same habit as adding a fixed wording error to the language lint.

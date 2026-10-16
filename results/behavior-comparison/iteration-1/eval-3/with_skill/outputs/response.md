I've made the Word file with the search strategy table. It has the concept table and a search result table (database, date searched, filters, syntax used, link). I filled in today's date, 12 Oct 2026, and left the links blank for you to add after you run the searches.

File: `search_strategy_ecommerce_indonesia.docx` (in the outputs folder, next to `spec.json`).

**Concepts:** (1) e-commerce and digital platforms, (2) adoption and use, (3) small businesses (SMEs, MSMEs, UMKM), (4) Indonesia (niche). Date range used: 2022 to 2026, the last five calendar years.

**Scopus**
```
TITLE-ABS-KEY((e-commerce OR ecommerce OR "electronic commerce*" OR "online shop*" OR "online selling*" OR "online marketplace*" OR "digital commerce*" OR "social commerce*" OR "digital platform*" OR Shopee OR Tokopedia OR Bukalapak) AND (adopt* OR accept* OR "technology adoption*" OR "intention to adopt" OR "intention to use" OR implement* OR utili?ation OR "digital transformation*" OR "digital adoption*" OR barrier* OR determinant* OR "success factor*") AND ("small business*" OR SME OR SMEs OR MSME OR MSMEs OR UMKM OR "small and medium enterprise*" OR "small and medium-sized enterprise*" OR "micro enterprise*" OR "small enterprise*" OR entrepreneur* OR "small firm*") AND (Indonesia* OR Jakarta OR Surabaya OR Bandung OR Yogyakarta OR Bali)) AND PUBYEAR > 2021 AND PUBYEAR < 2027
```

**Web of Science**
```
TS=((e-commerce OR ecommerce OR "electronic commerce*" OR "online shop*" OR "online selling*" OR "online marketplace*" OR "digital commerce*" OR "social commerce*" OR "digital platform*" OR Shopee OR Tokopedia OR Bukalapak) AND (adopt* OR accept* OR "technology adoption*" OR "intention to adopt" OR "intention to use" OR implement* OR utili?ation OR "digital transformation*" OR "digital adoption*" OR barrier* OR determinant* OR "success factor*") AND ("small business*" OR SME OR SMEs OR MSME OR MSMEs OR UMKM OR "small and medium enterprise*" OR "small and medium-sized enterprise*" OR "micro enterprise*" OR "small enterprise*" OR entrepreneur* OR "small firm*") AND (Indonesia* OR Jakarta OR Surabaya OR Bandung OR Yogyakarta OR Bali)) AND PY=(2022-2026)
```

**Google Scholar A**
```
(e-commerce OR "online marketplace" OR "electronic commerce" OR "digital platform") AND (adoption OR "intention to adopt" OR acceptance OR barriers) AND (SMEs OR MSMEs OR "small business" OR "small enterprises") AND Indonesia
```

**Google Scholar B** (platform and brand names)
```
(Shopee OR Tokopedia OR Bukalapak OR "social commerce" OR "online shop") AND (adoption OR "digital transformation" OR utilization OR determinants) AND (UMKM OR MSMEs OR "small business") AND (Indonesia OR Indonesian)
```

**Indonesian-language string** (Google Scholar, 235 characters, under the 256 limit)
```
("e-commerce" OR "toko online" OR "jual beli online" OR marketplace OR "transformasi digital") AND (adopsi OR penerimaan OR penggunaan OR pemanfaatan OR penerapan OR hambatan) AND (UMKM OR "usaha kecil" OR "pelaku usaha") AND Indonesia
```
It is also in the Word file. Run it as its own search and merge the results with the English ones. Don't join it to the English string with AND, because most good papers would drop out.

**Next steps**
- Run the strings. I can't open Scopus, Web of Science or Google Scholar, so none of them has been tested.
- Send me the hit counts. About 100 to 2,000 records in Scopus or Web of Science is workable. If it's higher, I'll tighten the adoption terms or the dates. If it's lower, I'll drop the small business concept first, then widen the Indonesia terms.
- Fill in the links in the result table once you have them. If you use Scholar, make sure the "Review articles" filter is off.
- I left out "Java" from the place names because it also matches the programming language.

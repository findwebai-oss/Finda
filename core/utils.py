import requests
import random
import re
import os
import difflib
from urllib.parse import urlparse, parse_qs, quote
from django.conf import settings
import time

CACHE = {}

# -------------------------
# TEXT NORMALIZATION & UTILS
# -------------------------
def normalize_title(title):
    text = title.lower()
    text = re.sub(r"[^a-z0-9çğıöşü ]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _query_tokens(query):
    text = normalize_title(query or "")
    tokens = [t for t in text.split() if len(t) > 1]
    stop = {"ve", "ile", "için", "icin", "the", "and", "or", "a", "an", "of", "for"}
    return [t for t in tokens if t not in stop]


def _is_relevant_title(title, query, min_match_ratio=0.6):
    title_norm = normalize_title(title or "")
    tokens = _query_tokens(query)
    if not tokens:
        return True
    matches = sum(1 for t in tokens if t in title_norm)
    return (matches / len(tokens)) >= min_match_ratio


def _relevance_score(title, query):
    title_norm = normalize_title(title or "")
    tokens = _query_tokens(query)
    if not tokens:
        return 0.0
    matches = sum(1 for t in tokens if t in title_norm)
    return matches / len(tokens)


def extract_real_link(google_link, title="", source=""):
    """
    Google'ın hapis linklerini kırar. 
    Eğer link temizlenemiyorsa, ilgili mağazanın arama sayfasına yönlendirir.
    """
    if not google_link or google_link == "#":
        return "#"
    
    source_lower = (source or "").lower()
    query_encoded = quote(title or "")

    # 1. Google içermiyorsa zaten direkt linktir
    if "google.com" not in google_link:
        return google_link

    # 2. URL Parametrelerini temizlemeyi dene
    try:
        parsed_url = urlparse(google_link)
        params = parse_qs(parsed_url.query)
        
        # 'adurl' veya 'url' parametreleri varsa çek
        for key in ['adurl', 'url', 'q']:
            if params.get(key):
                clean = params.get(key)[0]
                if clean.startswith("http"):
                    return clean
    except:
        pass

    # 3. ZORLAYICI MANTIK (Fallback): Google bizi bırakmıyorsa biz kendi linkimizi yaparız
    if "trendyol" in source_lower:
        return f"https://www.trendyol.com/sr?q={query_encoded}"
    elif "amazon" in source_lower:
        return f"https://www.amazon.com.tr/s?k={query_encoded}"
    elif "hepsiburada" in source_lower:
        return f"https://www.hepsiburada.com/ara?q={query_encoded}"
    elif "n11" in source_lower:
        return f"https://www.n11.com/arama?q={query_encoded}"
    elif "boyner" in source_lower:
        return f"https://www.boyner.com.tr/arama?q={query_encoded}"

    return google_link

# -------------------------
# SERP API (GÜÇLENDİRİLMİŞ)
# -------------------------
def fetch_serp_products(query, relax_filter=False):
    results = []
    api_key = getattr(settings, "SERP_API_KEY", os.getenv("SERP_API_KEY", "")).strip()

    if not api_key:
        print("SERP API KEY bulunamadı")
        return results

    params = {
        "engine": "google_shopping",
        "q": query,
        "api_key": api_key,
        "gl": "tr",
        "hl": "tr",
        "direct_link": "true"
    }

    try:
        response = requests.get("https://serpapi.com/search.json", params=params, timeout=10)
        data = response.json()
        shopping_results = data.get("shopping_results", [])

        for i, p in enumerate(shopping_results[:20]):
            p_id = f"serp_{i}_{random.randint(1000,9999)}"
            
            # Ham linki al
            raw_link = p.get("product_link") or p.get("direct_link")

            offers = p.get("offers")
            if not raw_link and offers and isinstance(offers, list) and len(offers) > 0:
                raw_link = offers[0].get("link")

            if not raw_link:
                raw_link = p.get("product_link") or p.get("link") or "#"

            # FİNDA DOKUNUŞU: Linki mağazaya zorla
            product_title = p.get("title", "")
            if not relax_filter and not _is_relevant_title(product_title, query, min_match_ratio=0.6):
                continue
            source_name = p.get("source", "")
            final_link = extract_real_link(raw_link, product_title, source_name)

            # Site Renkleri
            source_lower = source_name.lower()
            site_color = "warning"
            if "trendyol" in source_lower: site_color = "orange"
            elif "hepsiburada" in source_lower: site_color = "hb"
            elif "amazon" in source_lower: site_color = "amazon"
            elif "n11" in source_lower: site_color = "n11"
            elif "boyner" in source_lower: site_color = "boyner"

            results.append({
                "id": p_id,
                "title": product_title,
                "price": p.get("price", "Fiyat yok"),
                "image": p.get("thumbnail") or p.get("image"),
                "images": p.get("images") or ([p.get("thumbnail")] if p.get("thumbnail") else ([])),
                "brand": source_name,
                "rating": p.get("rating", 0),
                "review_count": p.get("reviews", 0),
                "reviews": p.get("reviews") if isinstance(p.get("reviews"), list) else [],
                "site": source_name,
                "site_color": site_color,
                "delivery_info": p.get("delivery", "Mağaza Detayı"),
                "positive_ratio": int(p.get("rating", 0) * 20) if p.get("rating") else 0,
                "review_summary": p.get("review_summary", ""),
                "description": p.get("snippet", ""),
                "link": final_link
            })
    except Exception as e:
        print("SerpAPI Error:", e)

    return results

# -------------------------
# DEMO APIs (FakeStore + DummyJSON)
# -------------------------
def fetch_demo_products(query):
    results = []
    query_words = _query_tokens(query)
    try:
        res = requests.get("https://fakestoreapi.com/products", timeout=5)
        for p in res.json():
            title_lower = p["title"].lower()
            if query_words:
                match_count = sum(1 for w in query_words if w in title_lower)
                if match_count / len(query_words) < 0.6:
                    continue
            results.append({
                "id": f"fs_{p['id']}",
                "title": p["title"],
                "price": f"{p['price']} $",
                "image": p["image"],
                "images": [p["image"]],
                "rating": p.get("rating", {}).get("rate", 0),
                "review_count": p.get("rating", {}).get("count", 0),
                "site": "FakeStore",
                "site_color": "primary",
                "delivery_info": "2-3 gün",
                "positive_ratio": int(p.get("rating", {}).get("rate", 0) * 20),
                "link": "#"
            })
    except: pass
    return results

# -------------------------
# DEDUPLICATION LOGIC
# -------------------------
def deduplicate_products(products):
    """Farklı mağazalardan gelen aynı ürünleri kaldır (başlığa göre)"""
    seen = set()
    unique = []
    
    for p in products:
        # Sadece title'a göre normalize et (site fark etmez)
        title_normalized = normalize_title(p.get("title", ""))
        
        # İlk 50 karakteri al (ürün ismi gerçekten benzerse algılanabilmesi için)
        key = title_normalized[:85]
        
        if key not in seen and key:  # Boş title almamak için
            seen.add(key)
            unique.append(p)
    
    return unique


def deduplicate_products_v2(products, similarity_threshold=0.84):
    unique = []

    for product in products:
        title = normalize_title(product.get("title", ""))
        if not title:
            continue
        is_duplicate = False
        for u in unique:
            u_title = normalize_title(u.get("title", ""))
            if not u_title:
                continue

            # Token overlap (fast check)
            tokens_a = set(title.split())
            tokens_b = set(u_title.split())
            if tokens_a and tokens_b:
                overlap = len(tokens_a & tokens_b) / max(1, len(tokens_a | tokens_b))
                if overlap < 0.55:
                    continue

            # Character-level similarity
            sm = difflib.SequenceMatcher(None, title, u_title)
            if sm.ratio() >= similarity_threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            unique.append(product)

    return unique


# -------------------------
# MAIN ENTRY
# -------------------------
def get_all_products(query, compare_mode=False):
    """
    query: Aranacak ürün/başlık
    compare_mode: True = Aynı ürün farklı satıcılardan (5 satıcı), 
                  False = Benzersiz ürünler (dedupe)
    """
    now = time.time()

    # cache varsa ve süresi geçmediyse
    cache_key = f"{query}_{compare_mode}"
    if cache_key in CACHE:
        cached_data, cached_time = CACHE[cache_key]
        if now - cached_time < 600:
            print("✅ CACHE'DEN GELDİ:", query, f"(compare_mode={compare_mode})")
            return cached_data
        else:
            del CACHE[cache_key]

    print("🌐 API'DEN GELDİ:", query, f"(compare_mode={compare_mode})")

    results = []
    serp_results = fetch_serp_products(query, relax_filter=False)
    if len(serp_results) < 5:
        serp_results = fetch_serp_products(query, relax_filter=True)
    results.extend(serp_results)

    if len(results) < 5:
        results.extend(fetch_demo_products(query))

    if compare_mode:
        # COMPARE MODE: Aynı ürünü satıcılardan getir (max 5, farklı mağaza)
        site_map = {}
        for r in results:
            site = r.get("site")
            if site and site not in site_map:
                site_map[site] = r
        results = list(site_map.values())[:5]
        print(f"📊 COMPARE MODE: {len(results)} satıcı bulundu")
    else:
        # NORMAL MODE: Duplicate ürünleri kaldır
        results = deduplicate_products_v2(results)
    
    # Sıra karıştır ama en iyileri yukarıya al (rating + review'e göre)
    results.sort(key=lambda x: (
        _relevance_score(x.get("title", ""), query),
        float(x.get("rating", 0)) or 0,
        int(str(x.get("review_count", 0)).replace(",", "")) or 0
    ), reverse=True)

    CACHE[cache_key] = (results, now)
    return results

# import requests
# import random
# import re
# import os
# import time
# from urllib.parse import urlparse, parse_qs, quote
# from django.conf import settings
# from rapidfuzz import fuzz

# CACHE = {}

# # -------------------------
# # TEXT NORMALIZATION
# # -------------------------
# def smart_normalize_title(title: str) -> str:
#     text = (title or "").lower()
#     text = re.sub(r"[^a-z0-9çğıöşü\.\-\+ ]", " ", text)
#     text = re.sub(r"\s+", " ", text).strip()
#     return text


# -------------------------
# # EXTRACT REAL LINK
# # -------------------------
# def extract_real_link(google_link, title="", source=""):
#     if not google_link or google_link == "#":
#         return "#"

#     source_lower = (source or "").lower()
#     query_encoded = quote(title or "")

#     # Eğer Google linki değilse direkt döndür
#     if "google.com" not in google_link:
#         return google_link

#     try:
#         parsed_url = urlparse(google_link)
#         params = parse_qs(parsed_url.query)

#         for key in ["adurl", "url", "q"]:
#             if params.get(key):
#                 clean = params.get(key)[0]
#                 if clean.startswith("http"):
#                     return clean
#     except:
#         pass

#     # Fallback: mağaza arama linki üret
#     if "trendyol" in source_lower:
#         return f"https://www.trendyol.com/sr?q={query_encoded}"
#     elif "amazon" in source_lower:
#         return f"https://www.amazon.com.tr/s?k={query_encoded}"
#     elif "hepsiburada" in source_lower:
#         return f"https://www.hepsiburada.com/ara?q={query_encoded}"
#     elif "n11" in source_lower:
#         return f"https://www.n11.com/arama?q={query_encoded}"
#     elif "boyner" in source_lower:
#         return f"https://www.boyner.com.tr/arama?q={query_encoded}"

#     return google_link


# # -------------------------
# # SERP API
# # -------------------------
# def fetch_serp_products(query):
#     results = []
#     api_key = getattr(settings, "SERP_API_KEY", os.getenv("SERP_API_KEY", "")).strip()

#     if not api_key:
#         print("SERP API KEY bulunamadı")
#         return results

#     params = {
#         "engine": "google_shopping",
#         "q": query,
#         "api_key": api_key,
#         "gl": "tr",
#         "hl": "tr",
#         "direct_link": "true"
#     }

#     try:
#         response = requests.get("https://serpapi.com/search.json", params=params, timeout=10)
#         data = response.json()
#         shopping_results = data.get("shopping_results", [])

#         for i, p in enumerate(shopping_results[:15]):
#             raw_link = p.get("product_link") or p.get("direct_link")

#             offers = p.get("offers")
#             if not raw_link and offers and isinstance(offers, list) and len(offers) > 0:
#                 raw_link = offers[0].get("link")

#             if not raw_link:
#                 raw_link = p.get("link") or "#"

#             product_title = p.get("title", "")
#             source_name = p.get("source", "")
#             final_link = extract_real_link(raw_link, product_title, source_name)

#             source_lower = source_name.lower()
#             site_color = "warning"
#             if "trendyol" in source_lower: site_color = "orange"
#             elif "hepsiburada" in source_lower: site_color = "hb"
#             elif "amazon" in source_lower: site_color = "amazon"
#             elif "n11" in source_lower: site_color = "n11"
#             elif "boyner" in source_lower: site_color = "boyner"

#             results.append({
#                 "id": f"serp_{i}_{random.randint(1000,9999)}",
#                 "title": product_title,
#                 "price": p.get("price", "Fiyat yok"),
#                 "image": p.get("thumbnail") or p.get("image"),
#                 "brand": source_name,
#                 "rating": p.get("rating", 0),
#                 "review_count": p.get("reviews", 0),
#                 "site": source_name,
#                 "site_color": site_color,
#                 "delivery_info": p.get("delivery", "Mağaza Detayı"),
#                 "positive_ratio": int(float(p.get("rating", 0)) * 20) if p.get("rating") else 0,
#                 "review_summary": "",
#                 "description": p.get("snippet", ""),
#                 "link": final_link
#             })

#     except Exception as e:
#         print("SerpAPI Error:", e)

#     return results


# # -------------------------
# # DEMO API
# # -------------------------
# def fetch_demo_products(query):
#     results = []
#     query_words = smart_normalize_title(query).split()

#     try:
#         res = requests.get("https://fakestoreapi.com/products", timeout=5)
#         for p in res.json():
#             title_norm = smart_normalize_title(p["title"])

#             if query_words and not all(word in title_norm for word in query_words):
#                 continue

#             results.append({
#                 "id": f"fs_{p['id']}",
#                 "title": p["title"],
#                 "price": f"{p['price']} $",
#                 "image": p["image"],
#                 "rating": p.get("rating", {}).get("rate", 0),
#                 "review_count": p.get("rating", {}).get("count", 0),
#                 "site": "FakeStore",
#                 "site_color": "primary",
#                 "delivery_info": "2-3 gün",
#                 "positive_ratio": int(float(p.get("rating", {}).get("rate", 0)) * 20),
#                 "link": "#"
#             })
#     except:
#         pass

#     return results


# # -------------------------
# # SMART DEDUPLICATION
# # -------------------------
# def deduplicate_products_v2(products, similarity_threshold=85):
#     unique = []

#     for product in products:
#         title = smart_normalize_title(product.get("title", ""))
#         site = product.get("site", "")

#         is_duplicate = False

#         for u in unique:
#             u_title = smart_normalize_title(u.get("title", ""))
#             u_site = u.get("site", "")

#             similarity = fuzz.token_sort_ratio(title, u_title)

#             if similarity >= similarity_threshold and site == u_site:
#                 is_duplicate = True
#                 break

#         if not is_duplicate:
#             unique.append(product)

#     return unique


# # -------------------------
# # MAIN ENTRY
# # -------------------------
# def get_all_products(query, compare_mode=False):
#     now = time.time()

#     normalized_query = smart_normalize_title(query)
#     cache_key = f"{normalized_query}_{compare_mode}"

#     if cache_key in CACHE:
#         cached_data, cached_time = CACHE[cache_key]
#         if now - cached_time < 600:
#             print("✅ CACHE'DEN GELDİ:", query, f"(compare_mode={compare_mode})")
#             return cached_data
#         else:
#             del CACHE[cache_key]

#     print("🌐 API'DEN GELDİ:", query, f"(compare_mode={compare_mode})")

#     results = []
#     results.extend(fetch_serp_products(query))

#     if len(results) < 5:
#         results.extend(fetch_demo_products(query))

#     if compare_mode:
#         site_map = {}
#         for r in results:
#             site = r.get("site")
#             if site and site not in site_map:
#                 site_map[site] = r
#         results = list(site_map.values())[:5]
#         print(f"📊 COMPARE MODE: {len(results)} satıcı bulundu")
#     else:
#         results = deduplicate_products_v2(results)

#     results.sort(
#         key=lambda x: (
#             float(x.get("rating", 0)) or 0,
#             int(str(x.get("review_count", 0)).replace(",", "")) or 0
#         ),
#         reverse=True
#     )

#     CACHE[cache_key] = (results, now)
#     return results

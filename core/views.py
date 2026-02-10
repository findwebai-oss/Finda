from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from .utils import get_all_products
from .ai_service import analyze_products
from .chat_service import analyze_user_message
from .intent import detect_flight_intent
from flights.services import search_flights

from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods

AIRLINE_NAMES = {
    "TK": "Türk Hava Yolları",
    "PC": "Pegasus",
    "XQ": "SunExpress",
    "VF": "AJet",
    "AJ": "AnadoluJet",
    "LH": "Lufthansa",
    "AF": "Air France",
    "BA": "British Airways",
    "KL": "KLM",
    "EK": "Emirates",
    "QR": "Qatar Airways",
    "EY": "Etihad",
}


def build_flight_summary(flight_results):
    data = flight_results.get("data") if isinstance(flight_results, dict) else None
    if not data:
        return ""
    cheapest = None
    cheapest_price = None
    for offer in data:
        try:
            price_total = float(offer.get("price", {}).get("total", 0))
        except (TypeError, ValueError):
            price_total = None
        if price_total is None:
            continue
        if cheapest_price is None or price_total < cheapest_price:
            cheapest_price = price_total
            cheapest = offer
    if not cheapest:
        return ""
    seg0 = cheapest.get("itineraries", [{}])[0].get("segments", [{}])[0]
    dep = (seg0.get("departure", {}) or {}).get("at", "")
    dep_time = dep[11:16] if len(dep) >= 16 else dep
    airline = (cheapest.get("validatingAirlineCodes") or [""])[0]
    currency = cheapest.get("price", {}).get("currency", "")
    duration = cheapest.get("itineraries", [{}])[0].get("duration", "")
    dur_text = duration.replace("PT", "").replace("H", "s ").replace("M", "dk").strip()
    segments = cheapest.get("itineraries", [{}])[0].get("segments", [])
    stops = max(0, len(segments) - 1)
    stop_text = "direkt" if stops == 0 else f"{stops} aktarma"
    airline_name = AIRLINE_NAMES.get(airline, airline)
    return f"En uygun uçuş {dep_time} saatinde, {airline_name} ile ({stop_text}, {dur_text}). Fiyat: {cheapest_price} {currency}"


def normalize_flight_results(flight_results):
    if not isinstance(flight_results, dict):
        return flight_results
    data = flight_results.get("data")
    if not isinstance(data, list):
        return flight_results
    for offer in data:
        code = (offer.get("validatingAirlineCodes") or [""])[0]
        offer["airline_code"] = code
        offer["airline_name"] = AIRLINE_NAMES.get(code, code or "Airline")
    return flight_results


@require_http_methods(["GET", "POST"])
def search_ajax(request):
    if request.GET.get("new_chat") == "true":
        if 'chat_history' in request.session:
            del request.session['chat_history']
        return HttpResponse("")

    if 'chat_history' not in request.session:
        request.session['chat_history'] = []

    chat_history = request.session['chat_history']
    user_message = request.POST.get("query", "") or request.GET.get("query", "")
    compare_mode = request.GET.get("compare") == "true" or request.POST.get("compare") == "true"
    site_filter = (request.POST.get("site", "") or request.GET.get("site", "")).strip().lower()

    # Flight state
    flight_form_data = request.session.get("flight_form_data", {})
    origin = request.POST.get("origin", "").strip().upper()
    destination = request.POST.get("destination", "").strip().upper()
    date = request.POST.get("date", "")
    adults_input = request.POST.get("adults", "1")

    # Flight form submission
    if origin and destination and date and not user_message:
        try:
            adults = int(adults_input) if adults_input else 1
            adults = max(1, adults)
        except (ValueError, TypeError):
            adults = 1

        flight_results = normalize_flight_results(search_flights(origin, destination, date, adults=adults))
        flight_ai_summary = build_flight_summary(flight_results)
        flight_form_data = {
            "origin": origin,
            "destination": destination,
            "date": date,
            "adults": adults
        }
        request.session["flight_results"] = flight_results
        request.session["flight_form_data"] = flight_form_data

        html = render_to_string("partials/result_block.html", {
            "flight_block": True,
            "flight_results": flight_results,
            "flight_ai_summary": flight_ai_summary,
            "flight_form_data": flight_form_data,
            "flight_intent_detected": False,
            "flight_query": "",
            "new_messages": []
        }, request=request)
        return HttpResponse(html)

    # Cache current length for delta blocks
    before_len = len(chat_history)

    # Flight intent detection
    if user_message and compare_mode:
        products = get_all_products(user_message, compare_mode=True)
        if site_filter:
            filtered = [p for p in products if site_filter not in (p.get("site", "") or "").lower()]
            if filtered:
                products = filtered

        if products:
            ai_summary = analyze_products(products)
            results = ai_summary.get("products", products)
            chat_history.append({
                'role': 'user',
                'content': user_message
            })
            chat_history.append({
                'role': 'assistant',
                'content': f'"{user_message}" için karşılaştırma sonuçları:',
                'compare_products': results,
                'compare_ai_summary': ai_summary
            })
            request.session['chat_history'] = chat_history
            request.session.modified = True

            new_messages = chat_history[before_len:]
            html = render_to_string("partials/result_block.html", {
                "flight_block": False,
                "flight_results": None,
                "flight_form_data": flight_form_data,
                "flight_intent_detected": False,
                "flight_query": "",
                "new_messages": new_messages
            }, request=request)
            return HttpResponse(html)

    if user_message:
        flight_check = detect_flight_intent(user_message)
        if flight_check['is_flight'] and flight_check['confidence'] > 0.7:
            html = render_to_string("partials/result_block.html", {
                "flight_block": True,
                "flight_results": None,
                "flight_ai_summary": "",
                "flight_form_data": flight_form_data,
                "flight_intent_detected": True,
                "flight_query": user_message,
                "new_messages": []
            }, request=request)
            return HttpResponse(html)

    # Normal chat/product flow
    results = []
    ai_summary = {}

    if user_message:
        chat_history.append({
            'role': 'user',
            'content': user_message
        })

        analysis = analyze_user_message(user_message, chat_history)

        if analysis.get('error'):
            chat_history.append({
                'role': 'assistant',
                'content': f"?zg?n?m, bir hata olu?tu: {analysis['error']}"
            })

        elif analysis['intent'] == 'shopping' and analysis.get('query'):
            query = analysis['query']
            products = get_all_products(query, compare_mode=compare_mode)

            if compare_mode and site_filter:
                filtered = [p for p in products if site_filter not in (p.get("site", "") or "").lower()]
                if filtered:
                    products = filtered

            if products:
                ai_result = analyze_products(products)
                results = ai_result.get("products", products)
                ai_summary = ai_result

                if compare_mode:
                    chat_history.append({
                        'role': 'assistant',
                        'content': analysis['response'] or f'"{query}" i?in kar??la?t?rma sonu?lar?:',
                        'compare_products': results,
                        'compare_ai_summary': ai_summary
                    })
                else:
                    chat_history.append({
                        'role': 'assistant',
                        'content': analysis['response'] or f'"{query}" i?in {len(results)} ?r?n buldum:',
                        'products': results,
                        'ai_summary': ai_summary
                    })

            else:
                chat_history.append({
                    'role': 'assistant',
                    'content': f'"{query}" i?in ?r?n bulunamad?. Ba?ka bir ?ey aramak ister misiniz?'
                })

        else:
            chat_history.append({
                'role': 'assistant',
                'content': analysis['response']
            })

        request.session['chat_history'] = chat_history
        request.session.modified = True

    new_messages = chat_history[before_len:]

    html = render_to_string("partials/result_block.html", {
        "flight_block": False,
        "flight_results": None,
        "flight_ai_summary": "",
        "flight_form_data": flight_form_data,
        "flight_intent_detected": False,
        "flight_query": "",
        "new_messages": new_messages
    }, request=request)
    return HttpResponse(html)



def home(request):
    if request.GET.get("new_chat") == "true":
        if 'chat_history' in request.session:
            del request.session['chat_history']
        if 'flight_results' in request.session:
            del request.session['flight_results']
        if 'flight_form_data' in request.session:
            del request.session['flight_form_data']
        if 'show_flight_section' in request.session:
            del request.session['show_flight_section']
        return redirect('home')

    if 'chat_history' not in request.session:
        request.session['chat_history'] = []

    chat_history = request.session['chat_history']
    user_message = request.POST.get("query", "") or request.GET.get("query", "")
    compare_mode = request.GET.get("compare") == "true"  # Deep analysis modu
    
    # Flight state (persist on page until new chat)
    flight_results = request.session.get("flight_results")
    flight_form_data = request.session.get("flight_form_data", {})
    show_flight_section = request.session.get("show_flight_section", False)
    flight_scroll = request.session.pop("flight_scroll", False)
    origin = request.POST.get("origin", "").strip().upper()
    destination = request.POST.get("destination", "").strip().upper()
    date = request.POST.get("date", "")
    adults_input = request.POST.get("adults", "1")
    
    # If flight form is submitted, process it
    if origin and destination and date and not user_message:
        try:
            adults = int(adults_input) if adults_input else 1
            adults = max(1, adults)
        except (ValueError, TypeError):
            adults = 1
        
        flight_results = normalize_flight_results(search_flights(origin, destination, date, adults=adults))
        flight_ai_summary = build_flight_summary(flight_results)
        flight_form_data = {
            "origin": origin,
            "destination": destination,
            "date": date,
            "adults": adults
        }
        show_flight_section = True
        request.session["flight_results"] = flight_results
        request.session["flight_form_data"] = flight_form_data
        request.session["show_flight_section"] = True
        request.session["flight_scroll"] = True

    # Check for flight intent - if detected, don't process as product search
    if user_message:
        flight_check = detect_flight_intent(user_message)
        if flight_check['is_flight'] and flight_check['confidence'] > 0.7:
            # This is a flight query, don't add to chat history for products
            show_flight_section = True
            request.session["show_flight_section"] = True
            return render(request, "home.html", {
                "chat_history": chat_history,
                "products": [],
                "ai_summary": {},
                "user_message": "",
                "compare_mode": compare_mode,
                "flight_intent_detected": True,
                "flight_query": user_message,
                "flight_results": None,
                "flight_ai_summary": "",
                "flight_form_data": flight_form_data,
                "show_flight_section": True
            })

    results = []
    ai_summary = {}

    if user_message:
        chat_history.append({
            'role': 'user',
            'content': user_message
        })

        analysis = analyze_user_message(user_message, chat_history)

        if analysis.get('error'):
            chat_history.append({
                'role': 'assistant',
                'content': f"Üzgünüm, bir hata oluştu: {analysis['error']}"
            })

        elif analysis['intent'] == 'shopping' and analysis.get('query'):
            query = analysis['query']
            products = get_all_products(query, compare_mode=compare_mode)

            if products:
                # 🔹 AI ürün etiketleme + analiz
                ai_result = analyze_products(products)

                results = ai_result.get("products", products)
                ai_summary = ai_result # Full result passes 'data', 'error', etc.

                if compare_mode:
                    # COMPARE MODE: Sonuncu assistant message'ına compare_products ekle
                    # Böyle orijinal products kaybolmaz
                    for msg in reversed(chat_history):
                        if msg.get('role') == 'assistant' and msg.get('products'):
                            msg['compare_products'] = results
                            msg['compare_ai_summary'] = ai_summary
                            break
                else:
                    # NORMAL MODE: Yeni message oluştur
                    chat_history.append({
                        'role': 'assistant',
                        'content': analysis['response'] or f'"{query}" için {len(results)} ürün buldum:',
                        'products': results,
                        'ai_summary': ai_summary
                    })

            else:
                chat_history.append({
                    'role': 'assistant',
                    'content': f'"{query}" için ürün bulunamadı. Başka bir şey aramak ister misiniz?'
                })

        else:
            chat_history.append({
                'role': 'assistant',
                'content': analysis['response']
            })

        request.session['chat_history'] = chat_history
        request.session.modified = True

    return render(request, "home.html", {
        "chat_history": chat_history,
        "results": results,      # etiketli ürünler
        "products": results,
        "ai_summary": ai_summary,  # AI JSON (highlights, pros, cons, verdict)
        "user_message": user_message,
        "compare_mode": compare_mode,
        "flight_results": flight_results,  # Flight search results if any
        "flight_ai_summary": build_flight_summary(flight_results) if flight_results else "",
        "flight_form_data": flight_form_data,  # Form values to repopulate
        "show_flight_section": show_flight_section,
        "flight_scroll": flight_scroll
    })

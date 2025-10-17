import json
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from .utils import PROFILES, stitch_segments, make_plots, convert_absolute_rows

def index(request):
    # PROFILES'ı burada kullanmıyoruz ama ileride sayfada gerekirse göndermek kolay olsun
    return render(request, "camapp/index.html", {"profiles": PROFILES})

def generate(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")
    try:
        payload = json.loads(request.body.decode("utf-8"))
        rows_abs = payload.get("rows", [])
        npts = int(payload.get("npts_per_seg", 100))

        # absolute -> delta dönüşümü
        rows = convert_absolute_rows(rows_abs)

        df = stitch_segments(rows, npts_per_seg=npts)
        if df is None or df.empty:
            return JsonResponse({"ok": False, "error": "No rows"})

        preview = df.head(100).to_dict(orient="records")
        img1, img2, img3 = make_plots(df)
        request.session["last_csv"] = df.to_csv(index=False)
        return JsonResponse({"ok": True, "preview": preview, "img1": img1, "img2": img2, "img3": img3})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)})

def export_csv(request):
    csv_str = request.session.get("last_csv")
    if not csv_str:
        return HttpResponseBadRequest("Önce Çiz ile veri üretin.")
    resp = HttpResponse(csv_str, content_type="text/csv")
    resp["Content-Disposition"] = 'attachment; filename="cam_profile.csv"'
    return resp

import json

from django.db.models import Count, F, Q, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.community.models import CommunityPost


def _serialize_post(post: CommunityPost) -> dict:
    profile = getattr(post.author, "profile", None)
    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "category": post.category,
        "author": profile.maple_nickname if profile else post.author.username,
        "authorLevel": 0,
        "views": post.views,
        "likes": post.likes,
        "comments": 0,
        "createdAt": post.created_at.isoformat(),
        "isRecommended": post.is_recommended,
    }


@csrf_exempt
@require_http_methods(["GET", "POST"])
def post_list(request) -> JsonResponse:
    if request.method == "GET":
        posts = CommunityPost.objects.select_related("author", "author__profile")
        category = request.GET.get("category", "all")
        search = request.GET.get("search", "").strip()
        sort_by = request.GET.get("sort", "latest")

        category_counts = {
            item["category"]: item["count"]
            for item in CommunityPost.objects.values("category").annotate(count=Count("id"))
        }

        if category != "all":
            if category not in CommunityPost.Category.values:
                return JsonResponse({"detail": "유효하지 않은 카테고리입니다."}, status=400)
            posts = posts.filter(category=category)
        if search:
            posts = posts.filter(Q(title__icontains=search) | Q(content__icontains=search))

        ordering = {
            "latest": "-created_at",
            "popular": "-popularity",
            "views": "-views",
        }
        if sort_by not in ordering:
            return JsonResponse({"detail": "유효하지 않은 정렬 기준입니다."}, status=400)
        if sort_by == "popular":
            posts = posts.annotate(popularity=Coalesce(F("likes"), Value(0)))
        posts = posts.order_by(ordering[sort_by], "-created_at")

        return JsonResponse(
            {
                "posts": [_serialize_post(post) for post in posts],
                "categoryCounts": {
                    "all": sum(category_counts.values()),
                    **category_counts,
                },
            }
        )

    if not request.user.is_authenticated:
        return JsonResponse({"detail": "로그인이 필요합니다."}, status=401)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"detail": "요청 형식이 올바르지 않습니다."}, status=400)

    title = str(body.get("title", "")).strip()
    content = str(body.get("content", "")).strip()
    category = body.get("category", CommunityPost.Category.FREE)
    if not title or not content:
        return JsonResponse({"detail": "제목과 내용을 입력해주세요."}, status=400)
    if len(title) > 200:
        return JsonResponse({"detail": "제목은 200자 이하여야 합니다."}, status=400)
    if category not in CommunityPost.Category.values:
        return JsonResponse({"detail": "유효하지 않은 카테고리입니다."}, status=400)

    post = CommunityPost.objects.create(
        author=request.user,
        title=title,
        content=content,
        category=category,
    )
    return JsonResponse({"post": _serialize_post(post)}, status=201)
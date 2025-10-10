import concurrent.futures
import time

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def make_request():
    """Один запрос к /topics"""
    start = time.perf_counter()
    r = client.get("/topics")
    elapsed = time.perf_counter() - start
    return r.status_code, elapsed


def test_stability_under_load():
    """NFR-06: При ~50 RPS ошибка-рейт ≤ 2 %."""
    total_requests = 500
    max_workers = 50  # имитируем 50 параллельных пользователей

    status_codes = []
    durations = []

    start_total = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        results = list(ex.map(lambda _: make_request(), range(total_requests)))

    total_time = time.perf_counter() - start_total

    for code, dur in results:
        status_codes.append(code)
        durations.append(dur)

    errors = sum(1 for code in status_codes if code >= 400)
    error_rate = errors / total_requests * 100
    avg_latency = sum(durations) / len(durations) * 1000

    print(f"\nВсего запросов: {total_requests}")
    print(f"Ошибок: {errors} ({error_rate:.2f}%)")
    print(f"Среднее время ответа: {avg_latency:.1f} мс")
    print(f"Средняя RPS: {total_requests / total_time:.1f}")

    assert error_rate <= 2, f"Слишком высокий error-rate: {error_rate:.2f}%"

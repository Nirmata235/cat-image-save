import requests
import json
import sys
import os


def get_cat_image_url(text):
    """Получение URL изображения кошки с текстом"""
    return f"https://cataas.com/cat/says/{text}"


def create_folder(token, folder_name):
    """Создание папки на Яндекс.Диске (если уже существует — игнорировать ошибку)"""
    url = "https://cloud-api.yandex.net/v1/disk/resources"
    headers = {"Authorization": f"OAuth {token}"}
    params = {"path": f"/{folder_name}"}

    response = requests.put(url, headers=headers, params=params)
    # 409 означает, что папка уже существует
    if response.status_code not in (201, 409):
        response.raise_for_status()


def upload_image_by_url(token, image_url, yandex_path):
    """Загрузка изображения на Яндекс.Диск по URL"""
    # 1. Ссылка для загрузки
    upload_url_api = "https://cloud-api.yandex.net/v1/disk/resources/upload"
    headers = {"Authorization": f"OAuth {token}"}
    params = {"path": yandex_path, "overwrite": "true"}

    resp = requests.get(upload_url_api, headers=headers, params=params)
    resp.raise_for_status()
    upload_href = resp.json()["href"]

    # 2. Загрузка содержимого изображения (без локального сохранения)
    img_resp = requests.get(image_url, stream=True)
    img_resp.raise_for_status()

    # Загрузка на Яндекс URL
    upload_resp = requests.put(upload_href, data=img_resp.content)
    upload_resp.raise_for_status()


def get_image_size(image_url):
    """Получение размера изображения"""
    resp = requests.get(image_url)
    resp.raise_for_status()
    return len(resp.content)


def main():

    text = input("Введите текст для картинки: ").strip()
    token = input("Введите токен Яндекс.Диска: ").strip()

    if not text or not token:
        print("Ошибка: текст и токен не могут быть пустыми.")
        sys.exit(1)

    group_name = "PY-160"  # Название группы в Нетологии
    filename = f"{text}.jpg"
    yandex_path = f"/{group_name}/{filename}"

    print(f"[1/3] Получение изображения для текста: {text}")
    image_url = get_cat_image_url(text)

    print(f"[2/3] Создание папки /{group_name} и загрузка файла...")
    try:
        create_folder(token, group_name)
        upload_image_by_url(token, image_url, yandex_path)
    except requests.HTTPError as e:
        print(f"Ошибка при работе с Яндекс.Диском: {e}")
        if e.response is not None:
            print(f"Детали: {e.response.text}")
        sys.exit(1)

    print(f"[3/3] Получение размера и сохранение result.json...")
    try:
        size_bytes = get_image_size(image_url)
    except Exception as e:
        print(f"Не удалось получить размер изображения: {e}")
        size_bytes = None

    result = {
        "filename": filename,
        "size_bytes": size_bytes
    }

    # Сохраняем result.json строго рядом с файлом main.py
    script_dir = os.path.dirname(os.path.abspath(__file__))
    result_path = os.path.join(script_dir, "result.json")

    # Читаем существующий список файлов, если result.json уже есть
    existing_data = []
    if os.path.exists(result_path):
        with open(result_path, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
                # Если вдруг там лежит старый формат (один словарь), оборачиваем его в список
                if isinstance(existing_data, dict):
                    existing_data = [existing_data]
            except json.JSONDecodeError:
                # Если файл пустой или поврежден, начинаем с пустого списка
                existing_data = []

    # Добавляем информацию о новой картинке
    existing_data.append(result)

    # Записываем обновленный список обратно в файл
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)

    print(f"Готово! Файл загружен на Яндекс.Диск, информация добавлена в {result_path}")


if __name__ == "__main__":
    main()
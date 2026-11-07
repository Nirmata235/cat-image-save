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


def save_to_json(filename, size_bytes):
    """Сохранение информации о файле в result.json (с накоплением)"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    result_path = os.path.join(script_dir, "result.json")

    existing_data = []
    if os.path.exists(result_path):
        with open(result_path, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
                if isinstance(existing_data, dict):
                    existing_data = [existing_data]
            except json.JSONDecodeError:
                existing_data = []

    existing_data.append({
        "filename": filename,
        "size_bytes": size_bytes
    })

    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)

    return result_path


def upload_image_by_url(token, image_url, yandex_path, filename):
    """Загрузка изображения на Яндекс.Диск по URL"""
    # 1. Получаем саму картинку
    img_resp = requests.get(image_url)
    img_resp.raise_for_status()
    image_data = img_resp.content
    size_bytes = len(image_data)  # Вот он, реальный размер загружаемого файла!

    # 2. Загружаем на Яндекс.Диск
    upload_url_api = "https://cloud-api.yandex.net/v1/disk/resources/upload"
    headers = {"Authorization": f"OAuth {token}"}
    params = {"path": yandex_path, "overwrite": "true"}

    # Cсылка для загрузки
    resp = requests.get(upload_url_api, headers=headers, params=params)
    resp.raise_for_status()
    upload_href = resp.json()["href"]

    # Отправляем файл по полученной ссылке
    upload_resp = requests.put(upload_href, data=image_data)
    upload_resp.raise_for_status()

    # 3. Сохраняем результат в JSON и возвращаем путь
    saved_path = save_to_json(filename, size_bytes)
    return saved_path, size_bytes


def main():
    # Входные данные
    text = input("Введите текст для картинки: ").strip()
    token = input("Введите токен Яндекс.Диска: ").strip()

    if not text or not token:
        print("Ошибка: текст и токен не могут быть пустыми.")
        sys.exit(1)

    group_name = "PY-160"  # Название вашей группы в Нетологии
    filename = f"{text}.jpg"
    yandex_path = f"/{group_name}/{filename}"

    print(f"[1/3] Получение изображения для текста: {text}")
    image_url = get_cat_image_url(text)

    print(f"[2/3] Создание папки /{group_name} и загрузка файла...")
    try:
        create_folder(token, group_name)
        saved_path, size_bytes = upload_image_by_url(token, image_url, yandex_path, filename)
    except requests.HTTPError as e:
        print(f"Ошибка при работе с Яндекс.Диском: {e}")
        if e.response is not None:
            print(f"Детали: {e.response.text}")
        sys.exit(1)

    print(f"[3/3] Успешно!")
    print(f"Готово! Файл {filename} (размер: {size_bytes} байт) загружен на Яндекс.Диск.")
    print(f"Информация добавлена в {saved_path}")


if __name__ == "__main__":
    main()
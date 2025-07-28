# 🗺️ План дальнейшей разработки (актуальный)

> Документ сфокусирован только на оставшихся задачах. Завершённые пункты из версии MVP удалены.

## 🍒 Критические задачи (следующие 2-3 спринта)

| ID | Задача | Ключевые шаги |
|----|--------|---------------|
| C1 | **Точная ML-сегментация почки** | • Подготовить датасет <br> • Обучить/интегрировать UNet (MONAI) <br> • Валидация на многоцентровых КТ <br> • Экспорт в `mask_to_gltf()` |
+<details>
+<summary>Подзадачи C1</summary>
+
+- **Сбор данных**
+  - Анонимизировать 50+ КТ-исследований
+  - Создать ground-truth маски почек (3D Slicer)
+- **Pre-processing**
+  - Пересэмплировать к изотропному вокселю (1 мм)
+  - Нормализовать HU диапазон (-100…400)
+- **Обучение**
+  - Запустить baseline 3D-UNet (MONAI) на RTX-GPU
+  - K-fold cross-validation → метрики Dice, HD95
+- **Инференс & интеграция**
+  - Экспорт модели → ONNX
+  - Обёртка `ml_inference.py` + fall-back CPU
+- **Post-processing**
+  - Морфология: fill-holes, largest-component
+  - Сглаживание mesh (Laplacian)
+- **Тесты / CI**
+  - Юнит-тест Dice ≥ 0.85 на hold-out наборе
</details>
|
| C2 | **Надёжная привязка 3-D модели к пациенту** | • Поддержка ArUco/AprilTag маркеров <br> • ICP-совмещение поверхности кожи (Open3D) <br> • UI-калибровка смещения, миллиметровый offset-log |
+<details>
+<summary>Подзадачи C2</summary>
+
+- **Визуальные маркеры**
+  - Добавить `OpenCV ArUco` детектор в Unity (NatCam/ARKit CVPixelBuffer)
+  - Калибровка физического размера маркера
+- **Сбор point-cloud**
+  - Захват depth/Lidar с устройства (ARKit LiDAR, ARCore Depth API)
+  - Фильтрация от шума
+- **Алгоритм ICP**
+  - Реализация через `Open3D.registration_icp`
+  - Ограничение по времени < 200 мс
+- **Интерфейс калибровки**
+  - Слайдеры X/Y/Z & yaw/pitch/roll
+  - Кнопка «Сохранить трансформ» → JSON
+- **Валидация**
+  - Phantom-тест: сравнить offset ≤ 5 мм
</details>
|
| C3 | **Оптимизация производительности AR** | • Полигональная редукция ≤ 50 k <br> • LOD / GPU профилирование Android+iOS <br> • Асинхронная загрузка GLB |
+<details>
+<summary>Подзадачи C3</summary>
+
+- Скрипт `simplify_mesh.py` (trimesh) – decimation ratio 0.3
+- Генерация LOD 0/1/2 + дист. переключения в Unity
+- Переход на `Addressables` для стриминга моделей
+- GPU Profiler: target ≥ 45 FPS на Snapdragon 888 / A15
+- Тест сцены с 3 моделями (stress) в CI (perf budget)
</details>
|
| C4 | **Защита мед. данных** | • Анонимизация DICOM в pipeline <br> • Логи без PHI <br> • Конфигурация прав доступа |
+<details>
+<summary>Подзадачи C4</summary>
+
+- Скрипт de-identify (pydicom remove tags + UID remap)
+- Хранение временных файлов в зашифрованной FS (optional)
+- Токен-аутентификация к API + role-based scopes
+- Audit-лог (user, timestamp, action) → CSV
</details>
|

## ⭐ Средний приоритет (до релиза 1.0)

| ID | Задача | Ключевые шаги |
|----|--------|---------------|
| M1 | **Улучшенный пользовательский поток** | Drag-&-Drop и PACS-pull <br> Пошаговый мастер в Unity |
+<details><summary>Подзадачи M1</summary>
+
+- Drag-drop виджет на Unity Canvas
+- PACS-pull: интеграция Orthanc REST `/studies` → выбор серии
+- Wizard UI: шаги Import → Segment → Align → AR
</details>
|
| M2 | **Расширенный алгоритм троакаров** | Учёт позы стола, соседних органов <br> Экспорт координат в DICOM SEG |
+<details><summary>Подзадачи M2</summary>
+
+- Добавить input: table tilt, patient orientation
+- Поддержка исключающих зон (печень, селезёнка) ← сегментация
+- Экспорт результата через `highdicom.Segmentation`
</details>
|
| M3 | **Расширенные тесты и CI** | Нагрузочные тесты больших томов <br> Unity WebGL build в GitHub Actions |
+<details><summary>Подзадачи M3</summary>
+
+- Генерировать synthetic 2 GB volume, стресс-тест RAM
+- Добавить pytest-benchmark stage
+- Настроить Game-CI шаг WebGL → upload artifact
</details>
|
| M4 | **Docker-стек для клиники** | Скрипт сборки `backend + Orthanc + Ngrok` |
+<details><summary>Подзадачи M4</summary>
+
+- Dockerfile с GPU-вариантом (CUDA)
+- docker-compose.prod.yml с env secrets
+- Ngrok authtoken + HTTPS tunnel script
</details>
|

## ▫️ Низкий приоритет / Backlog

| ID | Задача | Комментарий |
|----|--------|-------------|
| L1 | UI-полиш, темы, локализация | После основных клинических функций |
| L2 | Поддержка других органов (печень, селезёнка) | После успешного кейса «почка» |
| L3 | Кастомные PDF-отчёты клиники | Маркетинговый nice-to-have |
| L4 | Лицензирование / авто-обновления | Для коммерческого релиза |

import asyncio
import sys
from asyncio import sleep

from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QRadioButton, QTextEdit, QMessageBox, \
    QCheckBox
from playwright.async_api import async_playwright

from locator import loc_order_id, task, create_button, pay, count_do, pay_button
from script_context import get_context


class DebugWorker:
    async def debug_work_with_page(self, data):
        pass


class WorkerThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_running = False
        self.data_set = set()
        self.directory = None  # Добавляем атрибут для хранения directory

    def run(self):
        self.is_running = True
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        from script import work_with_page

        while self.is_running and self.data_set:
            data = self.data_set.pop()  # Получаем и удаляем один элемент из множества
            try:
                loop.run_until_complete(work_with_page(data, self.directory))
                self.progress.emit(1)
            except Exception as e:
                print(f"Произошла ошибка: {e}")
                self.progress.emit(0)
        loop.stop()
        loop.close()
        self.finished.emit()

    def set_data(self, data):
        self.data_set = set(data.split("===="))

    def stop(self):
        self.is_running = False


class RabbitFarmWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.unique_parts = set()
        self.worker_thread = WorkerThread()
        self.debug_worker = DebugWorker()
        self.directory = None  # Добавляем атрибут для хранения directory

    def on_radio_button_toggled(self):
        selected_radio_button = self.sender()
        if selected_radio_button.isChecked():
            service = selected_radio_button.text()
            self.directory = self.get_directory_for_service(service)  # Устанавливаем directory

    def update_progress(self, progress):
        if progress == 1:
            QMessageBox.information(self, "Успех", "Задача выполнена успешно!")
        else:
            QMessageBox.critical(self, "Ошибка", "Произошла ошибка при выполнении задачи.")

    def on_worker_finished(self):
        QMessageBox.information(self, "Завершено", "Все задачи выполнены.")

    def initUI(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f0e6fa;
                color: #333;
            }
            QPushButton {
                background-color: #007BFF;
                color: white;
                padding: 10px;
                margin: 5px;
                border-radius: 5px;
            }
            QPushButton:pressed {
                background-color: #0056b3;
            }
            QLineEdit {
                padding: 10px;
                margin: 5px;
                border-radius: 5px;
                border: 1px solid #333;
            }
            QRadioButton::indicator {
                width: 20px;
                height: 20px;
            }
        """)

        self.setWindowTitle('Хомячная ферма')
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        self.input_field = QTextEdit(self)
        self.input_field.setFixedWidth(450)
        self.input_field.setMinimumHeight(100)
        self.input_field.setStyleSheet("background-color: white; color: black;")
        layout.addWidget(self.input_field)

        self.start_button = QPushButton('Запуск', self)
        self.start_button.clicked.connect(self.on_start_clicked)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton('Стоп', self)
        self.stop_button.clicked.connect(self.on_stop_clicked)
        layout.addWidget(self.stop_button)

        self.radio_buttons = []
        for service in ['Джоб', '2 гис', 'Яндекс карты', 'Литрес']:
            radio_button = QRadioButton(service)
            radio_button.toggled.connect(self.on_radio_button_toggled)
            layout.addWidget(radio_button)
            self.radio_buttons.append(radio_button)

        self.debug_checkbox = QCheckBox('Дебаг активен', self)
        self.debug_checkbox.stateChanged.connect(self.on_debug_checkbox_changed)
        layout.addWidget(self.debug_checkbox)

        self.setLayout(layout)

    def on_start_clicked(self):
        if self.debug_checkbox.isChecked():
            asyncio.run(get_context())
        else:
            if not self.worker_thread.isRunning():
                if self.directory is None:
                    QMessageBox.critical(self, "Ошибка", "Выберите папку!")
                    return
                if self.input_field.toPlainText().strip() == "":
                    QMessageBox.critical(self, "Ошибка", "Введите текст!")
                    return
                self.worker_thread.set_data(self.input_field.toPlainText())
                self.worker_thread.directory = self.directory  # Передаем directory в поток
                self.worker_thread.start()

    def on_stop_clicked(self):
        self.worker_thread.stop()

    def on_debug_checkbox_changed(self, state):
        if state == Qt.Checked:
            # Optionally disable other controls if needed
            pass
        else:
            # Optionally re-enable other controls if needed
            pass

    def get_directory_for_service(self, service):
        loc = "//*[text() = '%s']"
        if service == 'Джоб':
            return loc % 'Джоб'
        elif service == '2 гис':
            return loc % '2 гис'
        elif service == 'Яндекс карты':
            return loc % 'Яндекс карты'
        elif service == 'Литрес':
            return loc % 'литрес'


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = RabbitFarmWindow()
    ex.show()
    sys.exit(app.exec_())


async def go_to_start_page(page):
    await page.goto("https://unu.im/tasks/orders")
    await sleep(1)


async def get_main_api(p):
    browser = await p.chromium.launch(headless=False)
    context = await browser.new_context(storage_state="context.json")
    page = await context.new_page()
    return browser, page


async def fill_task_and_create_task(page, data):
    await page.locator(task).clear()
    await page.locator(task).type(data, delay=1)
    await sleep(1)
    await page.locator(create_button).click()


async def put_final_param(page):
    await page.locator(pay).click()
    await sleep(1)
    await page.locator(count_do).fill("1")
    await sleep(1)


async def press_pay(page):
    await page.locator(pay_button).click()
    await sleep(1)


async def work_with_page(data, directory):
    async with async_playwright() as p:
        pass
        try:
            browser, page = await get_main_api(p)
            await go_to_start_page(page)
            await page.goto(await page.locator(directory + loc_order_id).get_attribute('href'))
            await fill_task_and_create_task(page, data)
            await put_final_param(page)
            await press_pay(page)
        except Exception as e:
            print(f"Произошла ошибка: {e}")
            raise
        finally:
            if browser:
                await browser.close()

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, select, insert, delete, update, func
from sqlalchemy.orm import declarative_base, Session
from datetime import datetime
from dash import Dash, callback, Input, Output, html, dcc, State, ALL, callback_context
import dash_bootstrap_components as dbc

# Определяем базу данных и создаем ее
engine = create_engine('sqlite:///tasks.db')
Base = declarative_base()

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    is_completed = Column(Boolean, default=False)

Base.metadata.create_all(engine)

# Функции для работы с БД
def get_all_tasks():
    """Список всех записей"""
    with Session(engine) as session:
        stmt = select(Task)
        result = session.scalars(stmt)
        return result.all()


def get_active_tasks():
    with Session(engine) as session:
        stmt = select(Task).where(Task.is_completed == False)
        result = session.scalars(stmt)
        return result.all()


def add_task(title):
    """Добавить новую запись"""
    with Session(engine) as session:
        stmt = insert(Task).values(title=title)
        session.execute(stmt)
        session.commit()


def delete_task(task_id):
    """Удалить запись"""
    with Session(engine) as session:
        stmt = delete(Task).where(Task.id == task_id)
        session.execute(stmt)
        session.commit()


def update_status(task_id):
    """Сменить статус"""
    with Session(engine) as session:
        row_stmt = select(Task).where(task_id == task_id)
        res = session.execute(row_stmt).scalars().first().is_completed
        change_status = False if res else True
        stmt = update(Task).where(Task.id == task_id).values(is_completed=change_status)
        session.execute(stmt)
        session.commit()


# Приложение
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.layout = dbc.Container([
    # общий заголовок приложения
    html.H1('Список задач', className='border-2 border-bottom py-3'),

    dbc.Row([
        # блок для вводна новой задачи (левая сторона)
        dbc.Col([
            html.H5('Новая задача', className='pt-3'),
            dbc.Input(id="add_input", placeholder='Добавить новую задачу'),
            dbc.Button(id='add_button', children='Добавить', class_name='mt-3')
        ], width=3),
        # блок для вывода задач (правая сторона)
        dbc.Col([
            dbc.Row([
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader('Всего задач', class_name='bg-primary text-white'),
                        dbc.CardBody(class_name='display-5', id='card_total')
                    ])
                ),
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader('Активных задач', class_name='bg-warning text-white'),
                        dbc.CardBody(class_name='display-5', id='card_active')
                    ])
                )
            ]),
            html.H5('Список задач', className='pt-3'),
            html.Div(id='task_list')
        ], width=9, class_name='border-2 border-start border-primary p-4'),
    ], class_name='h-100')
], class_name='vh-100')


# Обратные вызовы
@callback(
    Output('task_list', 'children'),
    Output('add_input', 'value'),
    Output('card_total', 'children'),
    Output('card_active', 'children'),
    Input({'type': 'btn', 'id': ALL}, 'n_clicks'),
    Input({'type': 'btn_change', 'id': ALL}, 'n_clicks'),
    Input('add_button', 'n_clicks'),
    State('add_input', 'value'),
)
def update_task_list(rm, upd, add_button, value):
    ctx = callback_context

    # DELETE VALUE
    if ctx.triggered_id is not None and any(rm):
        if ctx.triggered_id.type == 'btn':
            delete_task(ctx.triggered_id.id)

    # UPDATE STATUS
    if ctx.triggered_id is not None and any(upd):
        if ctx.triggered_id.type == 'btn_change':
            update_status(ctx.triggered_id.id)

    # ADD VALUE
    if value:
        add_task(value)

    # SELECT ALL
    all_tasks = get_all_tasks()

    # SELECT ACTIVE
    active_tasks = get_active_tasks()

    list_task = dbc.Table([
        html.Thead([
            html.Tr([
                *[html.Th(x) for x in ['ID', 'Задача', 'Статус', 'Действие']]
            ])
        ]),
        html.Tbody([
            # Правильное создание строк для каждой задачи
            html.Tr([
                html.Td(task.id),
                html.Td(task.title),
                html.Td('✅' if task.is_completed else '❌'),  # статус вместо created_at
                html.Td([
                    dbc.Button('Удалить', id={'type': 'btn', 'id': task.id}, class_name='btn-danger'),
                    dbc.Button('Изменить статус', id={'type': 'btn_change', 'id': task.id}, class_name='btn-warning ms-3'),
                ])
            ]) for task in all_tasks  # список строк для всех задач
        ])
    ], bordered=True, hover=True)
    return list_task, [], len(all_tasks), len(active_tasks)


if __name__ == '__main__':
    app.run(port=8501, host='0.0.0.0')
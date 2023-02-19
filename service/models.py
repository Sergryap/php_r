from django.db import models
from users.models import Customer, Freelancer


class Order(models.Model):
    status_choices = [
        ('1 not processed', 'Необработан'),
        ('2 selected', 'Выбран фрилансер'),
        ('3 performed', 'В работе'),
        ('4 completed', 'Выполнен'),
        ('5 expired', 'Просрочен')
    ]
    title = models.CharField(
        'Название заказа',
        max_length=300,
        blank=True
    )
    client = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='client_orders',
        verbose_name='Клиент',
    )
    freelancer = models.ForeignKey(
        Freelancer,
        on_delete=models.CASCADE,
        related_name='freelancer_orders',
        verbose_name='Фрилансер',
        null=True,
        blank=True
    )
    description = models.TextField(
        verbose_name='Описание заказа',
        max_length=100,
        null=True,
        blank=True
    )
    status = models.CharField(
        verbose_name='Статус',
        choices=status_choices,
        default='1 not processed',
        db_index=True,
        max_length=30,
    )
    created_at = models.DateTimeField(
        verbose_name='Время создания',
        auto_now_add=True
    )
    deadline = models.DateTimeField(
        verbose_name='Срок выполнения',
        null=True,
        blank=True
    )
    messages = models.TextField(
        verbose_name='Переписка по заказу',
        default=f'Переписка по заказу',
        null=True,
        blank=True
    )
    document = models.FileField(
        upload_to='order_documents/%Y/%m/%d/',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def __str__(self):
        return f'{self.client}_{self.freelancer}_{self.created_at}'
from django.db import models
from django.utils.translation import gettext as _

from core.models import BaseModel, TimeStampMixin
from usermodel.models import CustomUser


class CartModel(BaseModel, TimeStampMixin, models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    bus_id = models.CharField(max_length=15, verbose_name=_('bus_id'), null=True, blank=True)
    count_order = models.JSONField(_('count_order'),null=True, blank=True)
    size_order = models.JSONField(_('size_order'),null=True, blank=True)
    packages = models.JSONField(_('packages'),null=True, blank=True)
    packages_allocation = models.JSONField(_('packages_allocation'),null=True, blank=True)
    sizes = models.JSONField(_('sizes'),null=True, blank=True) 
    content = models.CharField(max_length=30, verbose_name=_('content'), null=True, blank=True)
    service = models.CharField(max_length=30, verbose_name=_('service'), null=True, blank=True)
    value = models.CharField(max_length=30, verbose_name=_('value'), null=True, blank=True)
    pickup_date = models.CharField(max_length=11, verbose_name=_('pickup_date'), null=True, blank=True)

    sender_title = models.CharField(_('sender_title'), max_length=50, null=True, blank=True)
    SenderAddress = models.CharField(_('sender_address'), max_length=200, null=True, blank=True)
    Senderpelak = models.CharField(_('sender_plaque'), max_length=20, null=True, blank=True)
    Sendervahed = models.CharField(_('sender_unity'), max_length=10, null=True, blank=True)
    SenderName = models.CharField(_('sender_name'), max_length=100, null=True, blank=True)
    SenderMobile = models.CharField(_('sender_phone'), max_length=11, null=True, blank=True)
    idcity_sender = models.CharField(_('sender_city'), max_length=10, null=True, blank=True)
    iddistrict_sender = models.CharField(_('sender_district'), max_length=50, null=True, blank=True)
    sender_map_link = models.URLField(_('sender_map_link'), null=True, blank=True)
    sender_zone = models.CharField(_('sender_zone'),max_length=20, null=True, blank=True)
    sender_lat = models.CharField(_('sender_lat'), max_length=20, null=True, blank=True)
    sender_long = models.CharField(_('sender_long'), max_length=20, null=True, blank=True)

    # receiver_title = models.CharField(_('receiver_title'), max_length=50, null=True, blank=True)
    # ReceiverAddress = models.CharField(_('receiver_address'), max_length=200, null=True, blank=True)
    # Receiverpelak = models.CharField(_('receiver_plaque'), max_length=20, null=True, blank=True)
    # Receivervahed = models.CharField(_('receiver_unity'), max_length=10, null=True, blank=True)
    # ReceiverName = models.CharField(_('receiver_name'), max_length=100, null=True, blank=True)
    # ReceiverMobile = models.CharField(_('receiver_phone'), max_length=11, null=True, blank=True)
    # idcity_resiver = models.CharField(_('receiver_city'), max_length=10, null=True, blank=True)
    # iddistrict_receiver = models.CharField(_('receiver_district'), max_length=50, null=True, blank=True)
    # receiver_map_link = models.URLField(_('receiver_map_link'), null=True, blank=True)
    # receiver_zone = models.CharField(_('receiver_zone'),max_length=20, null=True, blank=True)
    # receiver_lat = models.CharField(_('receiver_lat'), max_length=20, null=True, blank=True)
    # receiver_long = models.CharField(_('receiver_long'), max_length=20, null=True, blank=True)
    receiver_info = models.JSONField(_('receiver_info'), default=list,null=True, blank=True)

    Additional_details = models.TextField(_('address description'),null=True, blank=True)
    # discription = models.TextField(_('description'),null=True, blank=True)

    # open = models.BooleanField(_('open'), null=True, blank=True)
    saved = models.BooleanField(_('saved'), null=True, blank=True)
    # disabled = models.BooleanField(_('disabled'), null=True, blank=True)
    edit = models.BooleanField(_('edit'), null=True, blank=True)
    # packages_disable = models.BooleanField(_('packages_disable'), null=True, blank=True)
    # selected_Address = models.IntegerField(_('selected_Address'), null=True, blank=True)

    product_content=models.CharField(max_length=40, null=True, blank=True)
    product_value=models.IntegerField(_('product_value'), null=True, blank=True)
    price = models.IntegerField(_('price'), null=True, blank=True)
    total = models.IntegerField(_('total'), null=True, blank=True)
    service_name = models.CharField(max_length=100, verbose_name=_('service_name'), null=True, blank=True)
    is_multi = models.BooleanField(_('is_multi'), null=True, blank=True)
    pickup = models.CharField(max_length=100, verbose_name=_('pickup'), null=True, blank=True)
    delivery = models.CharField(max_length=100, verbose_name=_('delivery'), null=True,blank=True)
    

    def __str__(self):
        return self.user.username

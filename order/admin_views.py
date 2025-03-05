from jalali_date import date2jalali, datetime2jalali
from collections import defaultdict

from django.db.models import Min
from django.db.models import Sum
from rest_framework import permissions, generics, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from core.utils.permissions import get_user_permissions

from .admin_serializers import AdminOrderSerializer, AdminAllOrderSerializer
from .models import Order

class AdminOrdersPagination(PageNumberPagination):
    page_size = 50  # Adjust this according to how many orders you want per page
    page_size_query_param = 'page_size'  # Optional: Allow clients to specify page size
    # max_page_size = 5000  # You can adjust the max size if needed




class AdminOrdersView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AdminAllOrderSerializer
    pagination_class = AdminOrdersPagination

    def get_queryset(self):
        # Annotate each tracking_code with the minimum ID
        subquery = Order.objects.values('tracking_code').annotate(min_id=Min('id')).values_list('min_id', flat=True)
        # Fetch only the orders with minimum ID for each tracking_code
        queryset = Order.objects.filter(id__in=subquery).select_related('size').order_by('-created_at')
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Check user's permissions
        user_permissions = get_user_permissions(request.user)
        if 'view_order' not in user_permissions:
            return Response({"message": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        # Apply pagination
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(queryset, request)
        
        if result_page is not None:
            # 🔥 Here is the fix! Serialize the result_page first
            serializer = self.serializer_class(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    
class AdminOrderDetailsView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AdminOrderSerializer
    queryset = Order.objects.all()

    def list(self, request, *args, **kwargs):
        # Check user's permissions
        user_permissions = get_user_permissions(request.user)
        small_count, medium_count, big_count= 0, 0, 0
        if 'view_order' not in user_permissions:
            return Response({"message": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        response_data = []
        tracking_code = self.kwargs.get('tracking_code')
        if tracking_code:
            queryset = Order.objects.filter(tracking_code=tracking_code)
            for order in queryset:
                if order.size.title == 'کوچک':
                    small_count += order.count  # or set fixed value if needed
                elif order.size.title == 'متوسط':
                    medium_count += order.count
                elif order.size.title == 'بزرگ':
                    big_count += order.count

            # Sum the total count of all grouped orders
            total_count = sum(order.count for order in queryset)

            serialized_order = AdminOrderSerializer(order).data

                # Add extra fields to serialized data
            serialized_order.update({
                'tracking_code': tracking_code,
                'small_count': small_count,
                'medium_count': medium_count,
                'big_count': big_count,
                'count': total_count,
                'created_at': datetime2jalali(order.created_at).strftime("%Y/%m/%d %H:%M:%S"),
                'updated_at': datetime2jalali(order.updated_at).strftime("%Y/%m/%d %H:%M:%S"),
            })

            # Add serialized order to response data
            response_data.append(serialized_order)

        return Response(response_data, status=status.HTTP_200_OK)
    

class AdminOrderEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AdminOrderSerializer
    lookup_field = 'tracking_code'

    def get_queryset(self):
        tracking_code = self.kwargs.get('tracking_code')
        return Order.objects.filter(tracking_code=tracking_code)

    def get(self, request, *args, **kwargs):
        # Check user's permissions
        user_permissions = get_user_permissions(request.user)
        if 'view_order' not in user_permissions:
            return Response({"message": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        queryset = self.get_queryset()
        if not queryset.exists():
            return Response({"message": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        # Check user's permissions
        user_permissions = get_user_permissions(request.user)
        if 'change_order' not in user_permissions:
            return Response({"message": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        querysets = self.get_queryset()
        if not querysets.exists():
            return Response({"message": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        for queryset in querysets:
            serializer = self.get_serializer(queryset, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            print(serializer)
            updated_orders = serializer.save()
        return Response({'message': 'با موفقیت تغییر یافت'}, status=status.HTTP_200_OK)


class AdminOrderDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AdminOrderSerializer
    lookup_field = 'tracking_code'

    def get_queryset(self):
        tracking_code = self.kwargs.get('tracking_code')
        return Order.objects.filter(tracking_code=tracking_code)

    def delete(self, request, *args, **kwargs):
        # Check user's permissions
        user_permissions = get_user_permissions(request.user)
        if 'delete_order' not in user_permissions:
            return Response({"message": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        querysets = self.get_queryset()
        if not querysets.exists():
            return Response({"message": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        for queryset in querysets:
            queryset.delete()
        return Response({'message': 'با موفقیت حذف شد'}, status=status.HTTP_200_OK)
    

class EditableFieldsView(APIView):
    def get(self, request,*args, **kwargs):
        tracking_code = self.request.query_params.get('tracking_code')
        if not tracking_code:
            return Response({'message':'کد رهگیری ارسال نشده است'}, status=status.HTTP_400_BAD_REQUEST)
        order = Order.objects.filter(tracking_code=tracking_code)
        user_permissions = get_user_permissions(request.user)
        groups = self.request.user.groups
        fields = []

        if 'change_order' not in user_permissions:
            return Response({'message': 'اجازه تغییر ندارید'}, status=status.HTTP_403_FORBIDDEN)
        if groups.filter(name='logestic').exists():
            if order.first().pursuit == 'waiting for distribution':
                fields = ['dispatcher_reciever']
        elif groups.filter(name='business').exists():
            fields = ['pickup_date', 'order_description','pursuit','address_description', 'sender_address', 'sender_map_link', 'receiver_address', 'receiver_map_link']
            if order.first().pursuit == 'returned':
                fields.append('service')
        else:
            fields = ['id', 'pre_order', 'user_business', 'order_number', 'order_description', 'address_description', 
                    'package', 'size', 'count', 'content', 'service', 'value', 'pickup_date', 
                    'sender_title', 'sender_address', 'sender_plaque', 'sender_stage', 'sender_state', 
                    'sender_city', 'sender_district', 'sender_unity', 'sender_name', 'sender_phone', 
                    'sender_map_link', 'sender_lat', 'sender_long', 'sender_zone', 
                    'receiver_title', 'receiver_address', 'receiver_plaque', 'receiver_stage', 
                    'receiver_unity', 'receiver_state', 'receiver_city', 'receiver_district', 
                    'receiver_name', 'receiver_phone', 'receiver_map_link', 'receiver_lat', 
                    'receiver_long', 'receiver_zone', 'price', 'total_price', 'pursuit', 
                    'bank_code', 'tracking_code', 'delivery_code', 'is_multi', 'payment_status', 
                    'payment', 'credit', 'dispatcher_sender']
            
        return Response({'fields':fields}, status=status.HTTP_200_OK)
    


class NonEditableFieldsView(APIView):
    def get(self, request,*args, **kwargs):
        tracking_code = self.request.query_params.get('tracking_code')
        if not tracking_code:
            return Response({'message':'کد رهگیری ارسال نشده است'}, status=status.HTTP_400_BAD_REQUEST)
        order = Order.objects.filter(tracking_code=tracking_code)
        user_permissions = get_user_permissions(request.user)
        groups = self.request.user.groups
        fields = ['id', 'pre_order', 'user_business', 'order_number', 'order_description', 'address_description', 
                    'package', 'size', 'count', 'content', 'service', 'value', 'pickup_date', 
                    'sender_title', 'sender_address', 'sender_plaque', 'sender_stage', 'sender_state', 
                    'sender_city', 'sender_district', 'sender_unity', 'sender_name', 'sender_phone', 
                    'sender_map_link', 'sender_lat', 'sender_long', 'sender_zone', 
                    'receiver_title', 'receiver_address', 'receiver_plaque', 'receiver_stage', 
                    'receiver_unity', 'receiver_state', 'receiver_city', 'receiver_district', 
                    'receiver_name', 'receiver_phone', 'receiver_map_link', 'receiver_lat', 
                    'receiver_long', 'receiver_zone', 'price', 'total_price', 'pursuit', 
                    'bank_code', 'tracking_code', 'delivery_code', 'is_multi', 'payment_status', 
                    'payment', 'credit', 'dispatcher_sender', 'dispatcher_reciever']

        if 'change_order' not in user_permissions:
            if 'view_order' in user_permissions:
                return Response({'fields': fields}, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'اجازه تغییر ندارید'}, status=status.HTTP_403_FORBIDDEN)
            
        if groups.filter(name='logestic').exists():
            if order.first().pursuit == 'waiting for distribution':
                fields.remove('dispatcher_reciever')
        elif groups.filter(name='business').exists():
            for field in ['pickup_date', 'order_description','pursuit','address_description', 'sender_address', 'sender_map_link', 'receiver_address', 'receiver_map_link']:
                fields.remove(field)
            if order.first().pursuit == 'returned':
                fields.remove('service')
        else:
            fields = []
            
        return Response({'fields':fields}, status=status.HTTP_200_OK)


    
    

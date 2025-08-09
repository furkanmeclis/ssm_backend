from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from utils.api_responses import ApiResponse
from rest_framework.response import Response

class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data, message=None, additional_data=None):
        if not message:
            message = 'İşlem başarılı oldu.'
            
        response_data = {
            'success': True,
            'message': ApiResponse._format_message(message),
            'total': self.page.paginator.count,
            'page_size': self.page.paginator.per_page,
            'current_page': self.page.number,
            'total_pages': self.page.paginator.num_pages,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'data': data,
            'status_code': status.HTTP_200_OK
        }
        
        # Add any additional data if provided
        if additional_data:
            for key, value in additional_data.items():
                response_data[key] = value
                
        return Response(response_data, status=status.HTTP_200_OK)

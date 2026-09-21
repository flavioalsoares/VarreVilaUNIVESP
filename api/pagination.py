from rest_framework.pagination import PageNumberPagination


class PaginacaoPadrao(PageNumberPagination):
    """
    Vinte por página, mas o cliente pode pedir mais — até um teto.

    O mapa do site público precisa de todos os eventos geolocalizados de uma
    vez; obrigá-lo a percorrer páginas de vinte seria seis requisições para
    desenhar cem marcadores. O teto impede que alguém peça um milhão.
    """

    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 200

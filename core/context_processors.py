from django.conf import settings


def instituicao(request):
    """
    Injeta as variáveis institucionais em todos os templates.
    Para alterar o nome da instituição, edite INSTITUICAO_NOME em config/settings.py
    ou defina a variável de ambiente INSTITUICAO_NOME.
    """
    return {
        'INST_NOME': settings.INSTITUICAO_NOME,
        'INST_SUBTITULO': settings.INSTITUICAO_SUBTITULO,
        'INST_SLOGAN': settings.INSTITUICAO_SLOGAN,
        'INST_EMAIL': settings.INSTITUICAO_EMAIL,
        'INST_FACEBOOK': settings.INSTITUICAO_FACEBOOK,
        'INST_ANO_FUNDACAO': settings.INSTITUICAO_ANO_FUNDACAO,
        'INST_APROVA_1': settings.INSTITUICAO_APROVA_1,
        'INST_APROVA_2': settings.INSTITUICAO_APROVA_2,
        'INST_APROVA_3': settings.INSTITUICAO_APROVA_3,
    }

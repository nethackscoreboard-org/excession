from django.views.generic import TemplateView

class HomepageView(TemplateView):
    template_name = 'index.html'

class RulesView(TemplateView):
    template_name = 'rules.html'

class AboutView(TemplateView):
    template_name = 'about.html'

class ArchivesView(TemplateView):
    template_name = 'archives.html'

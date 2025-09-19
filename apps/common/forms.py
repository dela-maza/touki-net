# apps/common/forms.py
from flask_wtf import FlaskForm

class CSRFOnlyForm(FlaskForm):
    """
    CSRF検証だけ行う空フォーム
    Formクラスを使用しないでformを利用するページ（comform_delete,de
    """
    pass
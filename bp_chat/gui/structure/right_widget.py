from ..core.animate import *
from ..core.widgets import *
from ..models.list_model import ListView, ListModel, ListModelItem


class RightWidget(VLayoutWidget):

    def __init__(self, app, splitter):
        super().__init__(splitter)

        toolbar = Toolbar(self)
        self.addWidget(toolbar)

        def _show(*args):
            # w.a = fix_window(AnimatedDialog(w))
            # w.a.resize(200, 200)
            # w.a.exec_()
            pass

        toolbar.add_button("group", Toolbar.LEFT, "group").clicked.connect(
            lambda *args: app.exit(0))
        toolbar.add_label("title", Toolbar.CENTER, 'Title')
        toolbar.add_button("menu", Toolbar.RIGHT, "menu").clicked.connect(_show)

        info_label = InfoLabel(self)
        info_label.setText("Some info...")
        self.addWidget(info_label)

        #self.lay.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Expanding))

        self.toolbar = toolbar

        list_view = ListView(self)
        self.addWidget(list_view)

        # update_button = QPushButton("Update")
        # self.addWidget(update_button)

        self.list_model = ListModel(list_view)
        self.list_view = list_view
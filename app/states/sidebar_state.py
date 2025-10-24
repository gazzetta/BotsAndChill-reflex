import reflex as rx


class SidebarState(rx.State):
    is_open: bool = True

    @rx.event
    def toggle_sidebar(self):
        self.is_open = not self.is_open
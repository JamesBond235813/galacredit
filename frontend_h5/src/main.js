import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'

import {
  Button, Field, CellGroup, Form, Toast, Loading, NavBar, NoticeBar, Icon,
  Uploader, Dialog, Steps, Step, Empty, Tag, Popup,
  Tabbar, TabbarItem, Image as VanImage, Grid, GridItem, Cell, Checkbox
} from 'vant'
import 'vant/lib/index.css'

const app = createApp(App)

// Register Vant components.
app.use(Button).use(Field).use(CellGroup).use(Form).use(Toast).use(Loading)
   .use(NavBar).use(NoticeBar).use(Icon).use(Uploader).use(Dialog).use(Tag)
   .use(Steps).use(Step).use(Empty).use(Popup)
   .use(Tabbar).use(TabbarItem).use(VanImage).use(Grid).use(GridItem).use(Cell).use(Checkbox)

app.use(createPinia())
app.use(router)
app.mount('#app')

// Register only on HTTPS/localhost so Android Chrome can offer app installation.
if ('serviceWorker' in navigator && window.isSecureContext) {
  navigator.serviceWorker.register('/sw.js').catch(() => {})
}

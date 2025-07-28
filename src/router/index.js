import {createRouter, createWebHistory} from 'vue-router'
import Home from '../views/Home.vue'
import GameRoom from '../views/GameRoom.vue'

const routes = [
    {
        path: '/',
        name: 'Home',
        component: Home
    },
    {
        path: '/game/:sessionId',
        name: 'GameRoom',
        component: GameRoom,
        props: true
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router

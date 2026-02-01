import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi } from 'vitest'
import App from '../src/App.vue'

vi.mock('../src/services/api', () => ({
    getOperadoras: vi.fn(() => Promise.resolve({
        data: {
            data: [{ cnpj: '123', razao_social: 'Operadora Teste', modalidade: 'M', uf: 'SP' }],
            total: 1,
            page: 1,
            limit: 10
        }
    })),
    getStatsUF: vi.fn(() => Promise.resolve({ data: [] })),
    getOperadoraDespesas: vi.fn(() => Promise.resolve({ data: [] }))
}))

describe('App.vue', () => {
    it('deve renderizar o título do dashboard', () => {
        const wrapper = mount(App)
        expect(wrapper.find('h1').text()).toBe('IntuitiveCare Analytics')
    })

    it('deve carregar e exibir a lista de operadoras', async () => {
        const wrapper = mount(App)
        await flushPromises()
        expect(wrapper.text()).toContain('Operadora Teste')
    })
})

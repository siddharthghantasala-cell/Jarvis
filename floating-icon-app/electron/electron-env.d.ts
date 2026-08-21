/// <reference types="vite-plugin-electron/electron-env" />

declare namespace NodeJS {
  interface ProcessEnv {
    /**
     * The built directory structure
     *
     * ```tree
     * ├─┬─┬ dist
     * │ │ └── index.html
     * │ │
     * │ ├─┬ dist-electron
     * │ │ ├── main.js
     * │ │ └── preload.js
     * │
     * ```
     */
    APP_ROOT: string
    /** /dist/ or /public/ */
    VITE_PUBLIC: string
  }
}

// The API bridged into the Renderer process — must mirror `preload.ts`
interface IpcRendererApi {
  on(...args: Parameters<import('electron').IpcRenderer['on']>): void
  off(...args: Parameters<import('electron').IpcRenderer['off']>): void
  send(...args: Parameters<import('electron').IpcRenderer['send']>): void
  invoke(...args: Parameters<import('electron').IpcRenderer['invoke']>): Promise<unknown>

  // Recording API
  startRecording(): Promise<{ success: boolean; text?: string; error?: string }>
  stopAgent(): Promise<{ success: boolean; error?: string }>
}

// Used in Renderer process, exposed in `preload.ts`
interface Window {
  ipcRenderer: IpcRendererApi
}

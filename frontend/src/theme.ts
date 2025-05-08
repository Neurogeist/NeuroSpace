import { extendTheme } from '@chakra-ui/react'

export const theme = extendTheme({
  config: {
    initialColorMode: 'dark',
    useSystemColorMode: false,
  },
  styles: {
    global: {
      html: {
        overflowX: 'hidden',
      },
      body: {
        bg: 'gray.50',
        overflowX: 'hidden',
        width: '100%',
      },
    },
  },
}) 
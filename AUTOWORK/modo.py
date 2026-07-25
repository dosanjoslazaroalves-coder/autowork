import pyautogui
import time 
import logging 

import typing

class Modos :
      
      def __init__(self, pausa: float = 0.3): 
           self.pausa = pausa

      def mode_dev(self) -> None :
          pyautogui.press('win')
          time.sleep(self.pausa)
          pyautogui.write('visual estudio code')
          time.sleep(self.pausa)
          pyautogui.press('enter')

          time.sleep(self.pausa)
          pyautogui.press('win')
          time.sleep(self.pausa)
          pyautogui.write('codex')
          time.sleep(self.pausa)
          pyautogui.press('enter')
          
          time.sleep(self.pausa)
          pyautogui.press('win')
          time.sleep(self.pausa)
          pyautogui.write('pycharm')
          time.sleep(self.pausa)
          pyautogui.press('enter')

          time.sleep(self.pausa)
          pyautogui.press('win')
          time.sleep(self.pausa)
          pyautogui.write('intelliJ')
          time.sleep(self.pausa)
          pyautogui.press('enter')



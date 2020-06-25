class KeyEventMixin:
    __slots__ = ()

    def press_UNKNOWN(self):
        self.adb_shell("input keyevent 0")

    def press_SOFT_LEFT(self):
        self.adb_shell("input keyevent 1")

    def press_SOFT_RIGHT(self):
        self.adb_shell("input keyevent 2")

    def press_HOME(self):
        self.adb_shell("input keyevent 3")

    def press_BACK(self):
        self.adb_shell("input keyevent 4")

    def press_CALL(self):
        self.adb_shell("input keyevent 5")

    def press_ENDCALL(self):
        self.adb_shell("input keyevent 6")

    def press_0(self):
        self.adb_shell("input keyevent 7")

    def press_1(self):
        self.adb_shell("input keyevent 8")

    def press_2(self):
        self.adb_shell("input keyevent 9")

    def press_3(self):
        self.adb_shell("1input keyevent 0")

    def press_4(self):
        self.adb_shell("1input keyevent 1")

    def press_5(self):
        self.adb_shell("1input keyevent 2")

    def press_6(self):
        self.adb_shell("1input keyevent 3")

    def press_7(self):
        self.adb_shell("1input keyevent 4")

    def press_8(self):
        self.adb_shell("1input keyevent 5")

    def press_9(self):
        self.adb_shell("1input keyevent 6")

    def press_STAR(self):
        self.adb_shell("1input keyevent 7")

    def press_POUND(self):
        self.adb_shell("1input keyevent 8")

    def press_DPAD_UP(self):
        self.adb_shell("1input keyevent 9")

    def press_DPAD_DOWN(self):
        self.adb_shell("2input keyevent 0")

    def press_DPAD_LEFT(self):
        self.adb_shell("2input keyevent 1")

    def press_DPAD_RIGHT(self):
        self.adb_shell("2input keyevent 2")

    def press_DPAD_CENTER(self):
        self.adb_shell("2input keyevent 3")

    def press_VOLUME_UP(self):
        self.adb_shell("2input keyevent 4")

    def press_VOLUME_DOWN(self):
        self.adb_shell("2input keyevent 5")

    def press_POWER(self):
        self.adb_shell("2input keyevent 6")

    def press_CAMERA(self):
        self.adb_shell("2input keyevent 7")

    def press_CLEAR(self):
        self.adb_shell("2input keyevent 8")

    def press_A(self):
        self.adb_shell("2input keyevent 9")

    def press_B(self):
        self.adb_shell("3input keyevent 0")

    def press_C(self):
        self.adb_shell("3input keyevent 1")

    def press_D(self):
        self.adb_shell("3input keyevent 2")

    def press_E(self):
        self.adb_shell("3input keyevent 3")

    def press_F(self):
        self.adb_shell("3input keyevent 4")

    def press_G(self):
        self.adb_shell("3input keyevent 5")

    def press_H(self):
        self.adb_shell("3input keyevent 6")

    def press_I(self):
        self.adb_shell("3input keyevent 7")

    def press_J(self):
        self.adb_shell("3input keyevent 8")

    def press_K(self):
        self.adb_shell("3input keyevent 9")

    def press_L(self):
        self.adb_shell("4input keyevent 0")

    def press_M(self):
        self.adb_shell("4input keyevent 1")

    def press_N(self):
        self.adb_shell("4input keyevent 2")

    def press_O(self):
        self.adb_shell("4input keyevent 3")

    def press_P(self):
        self.adb_shell("4input keyevent 4")

    def press_Q(self):
        self.adb_shell("4input keyevent 5")

    def press_R(self):
        self.adb_shell("4input keyevent 6")

    def press_S(self):
        self.adb_shell("4input keyevent 7")

    def press_T(self):
        self.adb_shell("4input keyevent 8")

    def press_U(self):
        self.adb_shell("4input keyevent 9")

    def press_V(self):
        self.adb_shell("5input keyevent 0")

    def press_W(self):
        self.adb_shell("5input keyevent 1")

    def press_X(self):
        self.adb_shell("5input keyevent 2")

    def press_Y(self):
        self.adb_shell("5input keyevent 3")

    def press_Z(self):
        self.adb_shell("5input keyevent 4")

    def press_COMMA(self):
        self.adb_shell("5input keyevent 5")

    def press_PERIOD(self):
        self.adb_shell("5input keyevent 6")

    def press_ALT_LEFT(self):
        self.adb_shell("5input keyevent 7")

    def press_ALT_RIGHT(self):
        self.adb_shell("5input keyevent 8")

    def press_SHIFT_LEFT(self):
        self.adb_shell("5input keyevent 9")

    def press_SHIFT_RIGHT(self):
        self.adb_shell("6input keyevent 0")

    def press_TAB(self):
        self.adb_shell("6input keyevent 1")

    def press_SPACE(self):
        self.adb_shell("6input keyevent 2")

    def press_SYM(self):
        self.adb_shell("6input keyevent 3")

    def press_EXPLORER(self):
        self.adb_shell("6input keyevent 4")

    def press_ENVELOPE(self):
        self.adb_shell("6input keyevent 5")

    def press_ENTER(self):
        self.adb_shell("6input keyevent 6")

    def press_DEL(self):
        self.adb_shell("6input keyevent 7")

    def press_GRAVE(self):
        self.adb_shell("6input keyevent 8")

    def press_MINUS(self):
        self.adb_shell("6input keyevent 9")

    def press_EQUALS(self):
        self.adb_shell("7input keyevent 0")

    def press_LEFT_BRACKET(self):
        self.adb_shell("7input keyevent 1")

    def press_RIGHT_BRACKET(self):
        self.adb_shell("7input keyevent 2")

    def press_BACKSLASH(self):
        self.adb_shell("7input keyevent 3")

    def press_SEMICOLON(self):
        self.adb_shell("7input keyevent 4")

    def press_APOSTROPHE(self):
        self.adb_shell("7input keyevent 5")

    def press_SLASH(self):
        self.adb_shell("7input keyevent 6")

    def press_AT(self):
        self.adb_shell("7input keyevent 7")

    def press_NUM(self):
        self.adb_shell("7input keyevent 8")

    def press_HEADSETHOOK(self):
        self.adb_shell("7input keyevent 9")

    def press_FOCUS(self):
        self.adb_shell("8input keyevent 0")

    def press_PLUS(self):
        self.adb_shell("8input keyevent 1")

    def press_MENU(self):
        self.adb_shell("8input keyevent 2")

    def press_NOTIFICATION(self):
        self.adb_shell("8input keyevent 3")

    def press_SEARCH(self):
        self.adb_shell("8input keyevent 4")

    def press_MEDIA_PLAY_PAUSE(self):
        self.adb_shell("8input keyevent 5")

    def press_MEDIA_STOP(self):
        self.adb_shell("8input keyevent 6")

    def press_MEDIA_NEXT(self):
        self.adb_shell("8input keyevent 7")

    def press_MEDIA_PREVIOUS(self):
        self.adb_shell("8input keyevent 8")

    def press_MEDIA_REWIND(self):
        self.adb_shell("8input keyevent 9")

    def press_MEDIA_FAST_FORWARD(self):
        self.adb_shell("9input keyevent 0")

    def press_MUTE(self):
        self.adb_shell("9input keyevent 1")

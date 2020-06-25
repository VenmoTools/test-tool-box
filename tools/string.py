class String:

    @classmethod
    def first_word_upper(cls, key):
        """
        将单词的首字母大写
        :param key: 单词
        :return:
        """
        first_char = key[:1]
        return first_char.upper() + key[1:]

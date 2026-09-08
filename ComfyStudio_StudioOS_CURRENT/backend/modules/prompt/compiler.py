class PromptCompiler:


    def compile(shot):


        positive=f"""

电影级写实短剧镜头

人物:
{shot.get("character","")}

场景:
{shot.get("scene","")}

动作:
{shot.get("action","")}

比例:
9:16

24fps

"""

        negative="""

年龄错误

年代错误

现代设备

人物漂移

服装错误

"""

        return {

        "positive":positive,

        "negative":negative

        }


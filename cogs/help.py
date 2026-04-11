import discord
from discord.ext import commands
import json

class PaginationView(discord.ui.View):
    def __init__(self, embeds: list[discord.Embed]):
        super().__init__(timeout=300)
        self.embeds = embeds
        self.current_page = 0

        self.update_buttons()

    def update_buttons(self):
        if self.current_page == 0:
            self.children[0].disabled = True
        else:
            self.children[0].disabled = False

        if self.current_page == len(self.embeds) - 1:
            self.children[1].disabled = True
        else:
            self.children[1].disabled = False

    @discord.ui.button(label="◀️ Trước", style=discord.ButtonStyle.primary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self.update_buttons()

        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    @discord.ui.button(label="Sau ▶️", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self.update_buttons()

        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)


class help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cabin_channel = self.bot.config["cabin_channel"]
        self.sech_thu_id = self.bot.config["sech_thu"]
        self.announ_channel = self.bot.config["announ_channel"]

    @commands.command(name="help", aliases=['h'])
    async def help(self, ctx, command_name: str = None):
        if ctx.channel.id != self.cabin_channel:
            return

        if command_name:
            command_name =  command_name.lower()

        default = discord.Embed(title = "Các command có sẵn:")
        default.add_field(name = ">help hoặc >h", value = "Hiện ra bảng trợ giúp này", inline = False)
        default.add_field(name = ">batchuoc", value = "Bắt chước những gì người gửi nói \n Hãy gõ `>help batchuoc` để biết chi tiết thêm", inline = False)
        default.add_field(name = "/thongbao", value = "Thông báo cho các sếch thủ \n Hãy gõ `>help thongbao` để biết chi tiết thêm", inline = False)
        default.add_field(name = "/edit", value = "Chỉnh sửa thông báo \n Hãy gõ `>help edit` để biết chi tiết thêm", inline = False)
        default.add_field(name = "Extra: Phụ lục", value = "Phụ lục về syntax đối với Discord ID \n Hãy gõ `>help phuluc` để biết chi tiết thêm", inline = False)
        
        batchuoc = discord.Embed(title = "Command >batchuoc")
        batchuoc.add_field(name="Cú pháp", value = "**>batchuoc** `#tên channel` `nội dung còn lại`\nSau đó bạn có thể ghi thêm văn bản hoặc bất cứ file đính kèm nào, bot sẽ tự xử lý và bắt chước phần còn lại.")
        
        thongbao = discord.Embed(title = "Command /thongbao")
        thongbao.add_field(name = "Cú pháp", value = "**/thongbao** `channel` `caption` `mention` `title`  ...\n ", inline = False)
        thongbao.add_field(name = "Các loại tham số", value = f"""
        > `channel`: Kênh để gửi thông báo, mặc định là kênh <#{self.announ_channel}>
        > `caption`: Tiêu đề chính, nằm ngoài embed, khi ping được kích hoạt thì caption này sẽ hiện đầu tiên trong thông báo
        > `mention`: Mặc định sẽ ping <@&{self.sech_thu_id}>, nếu đặt là False thì sẽ không tự động ping
        > `title`: Tiêu đề embed
        > `description`: Mô tả embed, dùng để viết nội dung của truyện hay gì đó
        > `links`: Link của các trang, hãy tách ra bằng dấu cách, bot chỉ xử lý các link của vi-h, mimi và vinahentai
        > `cover`: Ảnh bìa của truyện hoặc thứ gì đó bạn muốn <@&{self.sech_thu_id}> thấy khi có thông báo
        > `archive`: Archive truyện (dưới dạng link Google Drive hoặc tương tự)
        > `archive_file`: Archive truyện (dạng file nén hoặc pdf)
        """, inline = False)
        
        edit = discord.Embed(title = "Command /edit (chỉ chỉnh sửa embed)")
        edit.add_field(name="Cú pháp", value = "**/edit** `message_link` `caption` `mention` `title` ...\n ", inline = False)
        edit.add_field(name = "Các loại tham số", value = f"""
        > `message_link` (**BẮT BUỘC**): Đường link tới tin nhắn để chỉnh sửa
        > `Các tham số còn lại`: Chỉnh sửa các nội dung tương ứng với command **/thongbao**
        **Lưu ý:** Nếu tham số được truyền vào bằng dấu chấm ("."), nội dung đó sẽ bị xoá 
        """)
        
        phu_luc = discord.Embed(title = "Phụ lục: Một số cú pháp đối với ID tin nhắn, roles ,người dùng,...")
        phu_luc.add_field(name = "Tổng quan về Discord ID", value = f"""
            i./ Để có thể lấy được ID của người dùng, bạn cần phải **bật chế độ Developer mode trong cài đặt của Discord**.
            ii./ ID của Discord sẽ có **18 chữ số**, bất kể là role, người, hay channel, emoji,...
            iii./ Trong kênh <#{self.cabin_channel}>, **một số** người, role hoặc kênh **Discord sẽ không tự đề xuất**, nên phải dùng ID để render
        """,inline = False)
        phu_luc.add_field(name = "1. Đối với người dùng", value = f"""
            Cú pháp để render ra tên user: `<@ID người dùng>`
            Ví dụ: `<@123456789012345678>`
            **Lưu ý:** Khi thông báo được gửi lên kênh công khai, **người dùng đó sẽ được ping**
        """, inline = False)
        phu_luc.add_field(name = "2. Đối với kênh", value = f"""
            Cú pháp để render ra kênh: `<#ID kênh>`
            Ví dụ: `<#123456789012345678>`
        """, inline= False)
        phu_luc.add_field(name = "3. Đối với role", value = f"""
            Cú pháp để render ra role: `<@&ID role>`
            Ví dụ: `<@&123456789012345678>`
            **Lưu ý**: Tương tự với ID người dùng, **tất cả những người có role đó cũng sẽ được ping**
        """, inline = False)
        
        list = [default, batchuoc, thongbao, edit, phu_luc]
        if command_name == "thongbao":
            await ctx.reply(embed = thongbao)
        elif command_name == "batchuoc":
            await ctx.reply(embed = batchuoc)
        elif command_name == "edit":
            await ctx.reply(embed = edit)
        elif command_name == "phuluc":
            await ctx.reply(embed = phu_luc)
        else:
            await ctx.reply(embed = list[0], view = PaginationView(embeds = list))

async def setup(bot):
    await bot.add_cog(help(bot))

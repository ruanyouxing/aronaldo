const { SlashCommandBuilder, PermissionFlagsBits, ChannelType } = require("discord.js");
const {
    COMMAND_CHANNEL_ID,
    ANNOUNCEMENT_CHANNEL_ID,
    serverId,
    ROLE_ID,
} = require("../config.json");
const { validateUrl } = require("../utils/validators");
const { createAnnouncementEmbed } = require("../utils/embedBuilder");

module.exports = {
    data: new SlashCommandBuilder()
        .setName("edit")
        .setDescription("Chỉnh sửa một thông báo đã đăng")
        .addStringOption((option) =>
            option.setName("message_id").setDescription("ID của tin nhắn cần sửa").

            setRequired(true),
        )
        .addChannelOption((option) =>
                option.setName("channel").setDescription("Kênh chứa tin nhắn cần sửa")
                    .addChannelTypes(ChannelType.GuildAnnouncement)
                    .setRequired(true),
            )
        .addStringOption((option) =>
            option.setName("title").setDescription("Tiêu đề mới").setRequired(false),
        )
        .addStringOption((option) =>
            option
                .setName("caption")
                .setDescription("Viết caption mới cho tin nhắn")
                .setRequired(false),
        )
        .addStringOption((option) =>
            option
                .setName("description")
                .setDescription("Nội dung/mô tả mới")
                .setRequired(false),
        )
        .addStringOption((option) =>
            option.setName("vi-h").setDescription("Link vi-h mới").setRequired(false),
        )
        .addStringOption((option) =>
            option.setName("mimi").setDescription("Link mimi mới").setRequired(false),
        )
        .addStringOption((option) =>
            option.setName("vinah").setDescription("Link vina mới").setRequired(false),
        )
        .addAttachmentOption((option) =>
            option.setName("cover").setDescription("File ảnh bìa mới").setRequired(false),
        )
        .addBooleanOption((option) =>
            option.setName("out_of_embed").setDescription("Ảnh bìa có nằm ngoài embed không?").setRequired(false),
        )
        .addStringOption((option) =>
            option
                .setName("archive")
                .setDescription("Link archive Google Drive mới")
                .setRequired(false),
        )
        .addAttachmentOption((option) =>
            option
                .setName("archive_file")
                .setDescription("Hoặc file rar archive mới")
                .setRequired(false),
        ),

    async execute(interaction) {
        // Sử dụng deferReply để có thêm thời gian xử lý và tìm tin nhắn
        await interaction.deferReply();

        // 1. Kiểm tra quyền hạn (Giống y hệt lệnh thongbao)
        const isAdmin = interaction.member.permissions.has(PermissionFlagsBits.Administrator);
        const hasPrivilegedRole = interaction.member.roles.cache.some((role) => role.id === ROLE_ID);

        if (!isAdmin && !hasPrivilegedRole) {
            return interaction.editReply({ content: `❌ Chưa tày đâu. Bạn phải là chủ pếch hoặc <@&${ROLE_ID}>.` });
        }

        if (interaction.channel.id !== COMMAND_CHANNEL_ID) {
            return interaction.editReply({ content: `❌ Bạn chỉ có thể dùng lệnh từ kênh <#${COMMAND_CHANNEL_ID}>` });
        }

        const messageId = interaction.options.getString("message_id");
        const outputChannel = interaction.options.getChannel("channel");

        if (!outputChannel) {
            return interaction.editReply({ content: `❌ Không tìm thấy kênh thông báo!` });
        }

        try {
            // 2. Lấy tin nhắn cũ
            const targetMessage = await outputChannel.messages.fetch(messageId);
            if (!targetMessage) {
                return interaction.editReply({ content: `❌ Không tìm thấy tin nhắn với ID \`${messageId}\`.` });
            }

            if (targetMessage.author.id !== interaction.client.user.id) {
                return interaction.editReply({ content: `❌ Bot chỉ có thể chỉnh sửa tin nhắn do chính nó gửi ra.` });
            }

            const oldEmbed = targetMessage.embeds[0];

            // 3. Trích xuất dữ liệu từ Embed cũ
            let oldLink1 = null, oldLink2 = null, oldLink3 = null, oldArchive = null;

            if (oldEmbed && oldEmbed.fields) {
                // Trích xuất Links
                const linkField = oldEmbed.fields.find((f) => f.name === "📎 Link");
                if (linkField) {
                    const l1Match = linkField.value.match(/\[Vi-h\]\((.*?)\)/);
                    if (l1Match) oldLink1 = l1Match[1];

                    const l2Match = linkField.value.match(/\[Mimi\]\((.*?)\)/);
                    if (l2Match) oldLink2 = l2Match[1];

                    const l3Match = linkField.value.match(/\[Vinahentai\]\((.*?)\)/);
                    if (l3Match) oldLink3 = l3Match[1];
                }

                // Trích xuất Archive
                const archiveField = oldEmbed.fields.find((f) => f.name === "📦 Archive");
                if (archiveField) {
                    const arcMatch = archiveField.value.match(/\[Xem archive truyện\]\((.*?)\)/);
                    if (arcMatch) oldArchive = arcMatch[1];
                }
            }

            // 4. Lấy dữ liệu người dùng nhập (Nếu không nhập thì dùng dữ liệu cũ)
            const newTitle = interaction.options.getString("title") ?? oldEmbed?.title ?? "Thông báo";
            const newDescription = interaction.options.getString("description") ?? oldEmbed?.description;
            const newCaption = interaction.options.getString("caption") ?? targetMessage.content;

            const link1 = interaction.options.getString("vi-h") ?? oldLink1;
            const link2 = interaction.options.getString("mimi") ?? oldLink2;
            const link3 = interaction.options.getString("vinah") ?? oldLink3;

            const newArchiveInput = interaction.options.getString("archive");
            const archiveFile = interaction.options.getAttachment("archive_file");

            // Nếu có input archive mới (link hoặc file) thì lấy cái mới, không thì giữ cái cũ
            const archiveUrl = archiveFile ? archiveFile.url : (newArchiveInput ?? oldArchive);

            // Validate URL cho các link mới nhập (Chỉ validate những link người dùng vửa truyền vào qua interaction)
            const inputsToValidate = [
                { name: "link1", url: interaction.options.getString("vi-h") },
                { name: "link2", url: interaction.options.getString("mimi") },
                { name: "link3", url: interaction.options.getString("vinah") },
                { name: "archive", url: newArchiveInput }
            ];

            for (const item of inputsToValidate) {
                if (item.url) {
                    const result = validateUrl(item.url);
                    if (!result.valid) {
                        return interaction.editReply({ content: `❌ URL bạn vừa nhập không hợp lệ (${item.name}): ${result.error}` });
                    }
                }
            }

            // Xử lý ảnh Cover
            const newCoverAttachment = interaction.options.getAttachment("cover");
            const newOutOfEmbedFlag = interaction.options.getBoolean("out_of_embed");

            let finalCoverUrl = null;
            let isOutOfEmbed = false;
            let editPayloadFiles = undefined; // Undefined nghĩa là giữ nguyên file đính kèm cũ của tin nhắn

            if (newCoverAttachment) {
                // Trường hợp 1: Có upload ảnh cover mới
                finalCoverUrl = newCoverAttachment.url;
                isOutOfEmbed = newOutOfEmbedFlag !== null ? newOutOfEmbedFlag : false;

                if (isOutOfEmbed) {
                    editPayloadFiles = [newCoverAttachment];
                } else {
                    editPayloadFiles = []; // Xóa hết attachment cũ vì ảnh đã chui vào trong embed
                }
            } else {
                // Trường hợp 2: Không upload ảnh cover mới -> Cố gắng giữ lại trạng thái cũ
                if (targetMessage.attachments.size > 0) {
                    // Tin nhắn cũ có ảnh nằm ngoài (Attachment)
                    const oldAttachment = targetMessage.attachments.first();
                    finalCoverUrl = oldAttachment.url;
                    isOutOfEmbed = newOutOfEmbedFlag !== null ? newOutOfEmbedFlag : true;

                    if (!isOutOfEmbed) {
                        // Người dùng muốn ép ảnh cũ chui vào trong Embed
                        editPayloadFiles = []; // Dọn attachment bên ngoài đi
                    }
                } else if (oldEmbed?.image?.url) {
                    // Tin nhắn cũ có ảnh nằm trong Embed
                    finalCoverUrl = oldEmbed.image.url;
                    isOutOfEmbed = newOutOfEmbedFlag !== null ? newOutOfEmbedFlag : false;
                    // Không thể chuyển ảnh từ trong Embed ra ngoài Attachment nếu người dùng không upload lại file
                    if (isOutOfEmbed) {
                        return interaction.editReply({ content: `❌ Bạn muốn đưa ảnh ra ngoài Embed nhưng lại không cung cấp file ảnh mới. Vui lòng upload lại file ở option \`cover\`.` });
                    }
                }
            }

            // 5. Tạo Embed mới bằng Builder có sẵn
            const updatedEmbed = createAnnouncementEmbed({
                title: newTitle,
                description: newDescription,
                link1: link1,
                link2: link2,
                link3: link3,
                cover: finalCoverUrl,
                archive: archiveUrl,
                outOfEmbed: isOutOfEmbed,
            });

            // 6. Cập nhật tin nhắn
            const editPayload = {
                content: newCaption !== null && newCaption !== "" ? newCaption : null,
                embeds: [updatedEmbed],
            };

            // Chỉ thay đổi thuộc tính files/attachments nếu có sự thay đổi về file
            if (editPayloadFiles !== undefined) {
                editPayload.files = editPayloadFiles;
                editPayload.attachments = []; // Bắt buộc dòng này để Discord dọn dẹp các file cũ không còn dùng
            }

            await targetMessage.edit(editPayload);

            await interaction.editReply({ content: `✅ Đã chỉnh sửa thành công tin nhắn tại https://discord.com/channels/${serverId}/${outputChannel.id}/${messageId} !` });

        } catch (error) {
            console.error("Error editing announcement:", error);

            // Bắt lỗi cụ thể nếu ID tin nhắn không tồn tại
            if (error.code === 10008) {
                return interaction.editReply({ content: "❌ Không tìm thấy tin nhắn! Hãy chắc chắn ID tin nhắn là đúng." });
            }

            await interaction.editReply({ content: "❌ Chỉnh sửa thất bại. Có lỗi xảy ra trong quá trình xử lý." });
        }
    },
};
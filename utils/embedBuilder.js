const { EmbedBuilder } = require("discord.js");

/**
 * Creates an embedded announcement message
 * @param {Object} options - The announcement options
 * @param {string} options.title - Main title
 * @param {string} options.description - Description text
 * @param {string} options.link1 - First link (required)
 * @param {string} options.link2 - Second link
 * @param {string} options.link3 - Third link
 * @param {string} options.cover - Cover image URL
 * @param {string} options.archive - Archive link
 * @param {string} options.fanpage - Fanpage link
 * @returns {EmbedBuilder} - The embedded message
 */
function createAnnouncementEmbed(options) {
  const {
    title,
    description,
    link1,
    link2,
    link3,
    cover,
    archive,
    fanpage,
  } = options;

  const embed = new EmbedBuilder()
    .setColor("#5865F2") // Discord blurple color
    .setTitle(title)
    .setTimestamp();

  // Add description if provided
  if (description) {
    embed.setDescription(description);
  }

  // Add cover image if provided
  if (cover) {
    embed.setImage(cover);
  }

  // Build links section
  let linksText = "";
  if (link1) {
    linksText += `🔗 [Link 1](${link1})\n`;
  }
  if (link2) {
    linksText += `🔗 [Link 2](${link2})\n`;
  }
  if (link3) {
    linksText += `🔗 [Link 3](${link3})\n`;
  }

  if (linksText) {
    embed.addFields({
      name: "📎 Links",
      value: linksText,
      inline: false,
    });
  }

  // Add archive and fanpage as inline fields
  if (archive || fanpage) {
    if (archive) {
      embed.addFields({
        name: "📦 Archive",
        value: `[View Archive](${archive})`,
        inline: true,
      });
    }
    if (fanpage) {
      embed.addFields({
        name: "👥 Fanpage",
        value: `[Visit Fanpage](${fanpage})`,
        inline: true,
      });
    }
  }

  return embed;
}

module.exports = {
  createAnnouncementEmbed,
};

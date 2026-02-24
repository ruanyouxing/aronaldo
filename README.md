# Discord Announcement Bot

A Discord bot that allows privileged users to post formatted announcements with links and images.

## Features

✅ Slash command `/thongbao` with autocomplete UI
✅ Role-based permissions (Administrator or "chủ pếch" role)
✅ Channel restrictions (command and output channels)
✅ Auto URL validation and normalization
✅ Professional embedded message formatting
✅ Multiple link support (up to 3 main links + archive + fanpage)
✅ Image attachment support
✅ Archive file attachment support (or URL)
✅ Ephemeral error messages (only visible to command user)
✅ Modular architecture

## Setup Instructions

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure the Bot

Edit `config.json` with your bot token and client ID:
```json
{
  "token": "YOUR_BOT_TOKEN",
  "clientId": "YOUR_CLIENT_ID"
}
```

### 3. Configure Channels

Edit `config/channels.js` to set your channel names:
- `COMMAND_CHANNEL`: Where users can run commands (default: "phòng-thí-nghiệm")
- `OUTPUT_CHANNEL`: Where bot posts announcements (default: "ếch-nhà-làm")

### 4. Configure Privileged Role

Edit `config/permissions.js` to set your privileged role name:
- `PRIVILEGED_ROLE`: Role name that can use commands (default: "chủ pếch")

**Note:** Users need either the privileged role OR Administrator permission to use commands.

### 5. Deploy Slash Commands

Register the slash commands with Discord:
```bash
node deploy-commands.js
```

### 6. Start the Bot

```bash
node index.js
```

## Usage

### Command: `/thongbao`

**Required Parameters:**
- `title` - Main title of the announcement
- `link1` - First link (required)

**Optional Parameters:**
- `description` - Description/details text
- `link2` - Second link
- `link3` - Third link
- `cover` - Cover image URL
- `archive` - Archive link (URL)
- `archive_file` - Archive file attachment (takes priority over archive URL)
- `fanpage` - Fanpage link

**Example:**
```
/thongbao 
  title: New Release Available!
  link1: https://example.com/download
  description: Check out our latest update
  cover: https://example.com/image.png
  archive_file: [Upload a file]
```

**Note:** For the `archive` parameter, you can either:
- Provide a URL using the `archive` option, OR
- Upload a file using the `archive_file` option
- If both are provided, the file attachment takes priority

## Permissions

Users need one of the following to use commands:
- **Administrator** permission, OR
- **"chủ pếch"** role (configurable in `config/permissions.js`)

## Channel Configuration

- Commands only work in the **command channel** (default: "phòng-thí-nghiệm")
- Announcements are posted to the **output channel** (default: "ếch-nhà-làm")
- Error messages are ephemeral (only visible to the user who ran the command)

## Project Structure

```
aronaldo-master/
├── commands/              # Command handlers
│   └── thongbao.js       # /thongbao command
├── config/               # Configuration files
│   ├── channels.js       # Channel names
│   └── permissions.js    # Permission settings
├── utils/                # Utility modules
│   ├── validators.js     # URL validation
│   └── embedBuilder.js   # Embed message builder
├── config.json           # Bot credentials
├── deploy-commands.js    # Command deployment script
├── index.js             # Main entry point
└── package.json         # Dependencies
```

## Troubleshooting

### Commands not appearing in Discord
- Run `node deploy-commands.js` to register commands
- Global commands can take up to 1 hour to propagate
- Make sure your bot token and client ID are correct

### Bot not responding
- Check that the bot is online in your server
- Verify the bot has proper permissions in both channels
- Check console for error messages

### Permission errors
- Ensure users have the "chủ pếch" role or Administrator permission
- Verify the role name matches exactly in `config/permissions.js`

### Channel errors
- Create channels with exact names: "phòng-thí-nghiệm" and "ếch-nhà-làm"
- Or update channel names in `config/channels.js` to match your server

## License

MIT

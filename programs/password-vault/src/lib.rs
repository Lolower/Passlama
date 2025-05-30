use anchor_lang::prelude::*;

declare_id!("7zQRzCwC9sL5iHUdpkggFSGKcqq6THhNTWSdTrJyaoax");

#[program]
pub mod password_vault {
    use super::*;

    pub fn initialize(
        ctx: Context<Initialize>,
        data: [u8; 109],
        data_len: u32,
        bump: u8,
    ) -> Result<()> {
        let account = &mut ctx.accounts.storage_account;

        if !account.is_initialized {
            require!(data_len as usize <= 109, ErrorCode::DataTooLarge);

            account.is_initialized = true;
            account.data.fill(0);
            let len = data_len as usize;
            account.data[..len].copy_from_slice(&data[..len]);
            account.data_len = data_len;
            account.bump = bump;

            msg!("Account initialized with data_len: {}", data_len);
        } else {
            msg!("Account already initialized. Skipping write.");
        }

        Ok(())
    }

    pub fn update_password(
        ctx: Context<UpdatePassword>,
        data: [u8; 109],
        data_len: u32,
    ) -> Result<()> {
        let account = &mut ctx.accounts.storage_account;

        require!(account.is_initialized, ErrorCode::AccountNotInitialized);
        require!(data_len as usize <= 109, ErrorCode::DataTooLarge);

        account.data.fill(0);
        let len = data_len as usize;
        account.data[..len].copy_from_slice(&data[..len]);
        account.data_len = data_len;

        msg!("Password updated. data_len: {}", data_len);

        Ok(())
    }
}

#[derive(Accounts)]
#[instruction()]
pub struct Initialize<'info> {
    #[account(
        init_if_needed,
        payer = payer,
        space = 8 + 1 + 1024 + 4 + 1,
        seeds = [payer.key().as_ref(), b"password_vault"],
        bump
    )]
    pub storage_account: Account<'info, StorageAccount>,
    #[account(mut)]
    pub payer: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct UpdatePassword<'info> {
    #[account(
        mut,
        seeds = [payer.key().as_ref(), b"password_vault"],
        bump = storage_account.bump
    )]
    pub storage_account: Account<'info, StorageAccount>,
    #[account(mut)]
    pub payer: Signer<'info>,
}

#[account]
pub struct StorageAccount {
    pub is_initialized: bool,
    pub data: [u8; 1024],
    pub data_len: u32,
    pub bump: u8,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Account already initialized")]
    AlreadyInitialized,
    #[msg("Account is not initialized")]
    AccountNotInitialized,
    #[msg("Data size exceeds maximum allowed")]
    DataTooLarge,
}

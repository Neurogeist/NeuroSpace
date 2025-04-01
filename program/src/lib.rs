use borsh::{BorshDeserialize, BorshSerialize};
use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint,
    entrypoint::ProgramResult,
    log::sol_log_compute_units,
    msg,
    program_error::ProgramError,
    pubkey::Pubkey,
};

// Declare and export the program's entrypoint
entrypoint!(process_instruction);

// Program entrypoint implementation
pub fn process_instruction(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    msg!("NeuroChain program entrypoint");

    let instruction = PromptInstruction::try_from_slice(instruction_data)
        .map_err(|_| ProgramError::InvalidInstructionData)?;

    match instruction {
        PromptInstruction::SubmitPrompt { prompt } => {
            msg!("Instruction: SubmitPrompt");
            process_submit_prompt(program_id, accounts, prompt)
        }
        PromptInstruction::SubmitResponse { response } => {
            msg!("Instruction: SubmitResponse");
            process_submit_response(program_id, accounts, response)
        }
    }
}

#[derive(BorshSerialize, BorshDeserialize, Debug)]
pub enum PromptInstruction {
    SubmitPrompt { prompt: String },
    SubmitResponse { response: String },
}

#[derive(BorshSerialize, BorshDeserialize, Debug)]
pub struct PromptAccount {
    pub prompt: String,
    pub response: Option<String>,
    pub is_processed: bool,
}

fn process_submit_prompt(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    prompt: String,
) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let prompt_account = next_account_info(account_info_iter)?;

    if !prompt_account.is_writable {
        msg!("Prompt account must be writable");
        return Err(ProgramError::InvalidAccountData);
    }

    if prompt_account.owner != program_id {
        msg!("Prompt account must be owned by the program");
        return Err(ProgramError::IncorrectProgramId);
    }

    let mut prompt_data = PromptAccount {
        prompt,
        response: None,
        is_processed: false,
    };

    prompt_data.serialize(&mut &mut prompt_account.data.borrow_mut()[..])?;
    msg!("Prompt submitted successfully");
    Ok(())
}

fn process_submit_response(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    response: String,
) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let prompt_account = next_account_info(account_info_iter)?;

    if !prompt_account.is_writable {
        msg!("Prompt account must be writable");
        return Err(ProgramError::InvalidAccountData);
    }

    if prompt_account.owner != program_id {
        msg!("Prompt account must be owned by the program");
        return Err(ProgramError::IncorrectProgramId);
    }

    let mut prompt_data: PromptAccount = BorshDeserialize::try_from_slice(&prompt_account.data.borrow())?;
    
    if prompt_data.is_processed {
        msg!("Prompt already processed");
        return Err(ProgramError::InvalidAccountData);
    }

    prompt_data.response = Some(response);
    prompt_data.is_processed = true;

    prompt_data.serialize(&mut &mut prompt_account.data.borrow_mut()[..])?;
    msg!("Response submitted successfully");
    Ok(())
} 
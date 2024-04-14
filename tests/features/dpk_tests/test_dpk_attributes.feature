Feature: DPK attributes api

  Background:
    Given Platform Interface is initialized as dlp and Environment is set according to git branch

  @DAT-64115
  Scenario: Get dpk attributes
    When I send "get" gen_request with "dpk_attributes" params
    Then I validate attributes response in context.req
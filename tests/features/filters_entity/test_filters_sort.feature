Feature: Sorting items and annotations

  Background: Initiate Platform Interface and create a project
    Given Platform Interface is initialized as dlp and Environment is set according to git branch
    And I create a project by the name of "items_sort"
    And I create dataset and items for sorting tests

  Scenario Outline: Sort items by <field> in <order> order
    When I list items sorted by <field> in <order> order
    Then the items should be sorted by <field> in <order> order

    Examples:
      | field      | order      |
      | name       | ascending  |
      | name       | descending |
      | created_at | ascending  |
      | created_at | descending |
      | updated_at | ascending  |
      | updated_at | descending |

  Scenario Outline: Sort items by <field> in <order> order with paging
    When I list items sorted by <field> in <order> order with page size 10
    Then the items across all pages should be sorted by <field> in <order> order

    Examples:
      | field      | order      |
      | name       | ascending  |
      | name       | descending |
      | created_at | ascending  |
      | created_at | descending |
      | updated_at | ascending  |
      | updated_at | descending |

  Scenario Outline: Sort annotations by <field> in <order> order
    When I list annotations sorted by <field> in <order> order
    Then the annotations should be sorted by <field> in <order> order

    Examples:
      | field      | order      |
      | created_at | ascending  |
      | created_at | descending |
      | type       | ascending  |
      | type       | descending |

  Scenario Outline: Sort annotations by <field> in <order> order with paging
    When I list annotations sorted by <field> in <order> order with page size 10
    Then the annotations across all pages should be sorted by <field> in <order> order

    Examples:
      | field      | order      |
      | created_at | ascending  |
      | created_at | descending |
      | type       | ascending  |
      | type       | descending |
